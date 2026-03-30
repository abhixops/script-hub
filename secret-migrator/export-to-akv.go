package main

import (
	"context"
	"encoding/csv"
	"io"
	"log"
	"os"
	"strings"
	"time"

	"github.com/Azure/azure-sdk-for-go/sdk/azidentity"
	"github.com/Azure/azure-sdk-for-go/sdk/keyvault/azsecrets"
)

var keyVaultName = "Azure key Vault name" // TODO: change this

func main() {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
	defer cancel()

	// -------- Azure Auth (uses az login automatically) --------
	cred, err := azidentity.NewDefaultAzureCredential(nil)
	if err != nil {
		log.Fatalf("Azure auth failed: %v", err)
	}

	vaultURL := "https://" + keyVaultName + ".vault.azure.net/"

	client, err := azsecrets.NewClient(vaultURL, cred, nil)
	if err != nil {
		log.Fatalf("Failed to create Azure client: %v", err)
	}

	log.Println("✅ Connected to Azure Key Vault")

	// -------- Open CSV --------
	file, err := os.Open("secrets.csv")
	if err != nil {
		log.Fatalf("Failed to open CSV: %v", err)
	}
	defer file.Close()

	reader := csv.NewReader(file)

	// Read header
	_, err = reader.Read()
	if err != nil {
		log.Fatalf("Failed to read CSV header: %v", err)
	}

	success := 0
	failed := 0

	// -------- Stream CSV (better for large files) --------
	for {
		record, err := reader.Read()

		if err == io.EOF {
			break
		}
		if err != nil {
			log.Printf("❌ CSV read error: %v", err)
			failed++
			continue
		}

		if len(record) < 3 {
			log.Printf("❌ Invalid row: %v", record)
			failed++
			continue
		}

		path := record[0]
		key := record[1]
		value := record[2]

		// Normalize name for Azure
		secretName := normalizeName(path + "-" + key)

		// Prepare request (NEW SDK format)
		params := azsecrets.SetSecretParameters{
			Value: &value,
			Tags: map[string]*string{
				"source": toPtr("vault"),
				"path":   toPtr(path),
			},
		}

		// Upload secret
		_, err = client.SetSecret(ctx, secretName, params, nil)
		if err != nil {
			log.Printf("❌ Failed: %s → %v", secretName, err)
			failed++
			continue
		}

		log.Printf("✔ Uploaded: %s", secretName)
		success++
	}

	log.Println("---------- Summary ----------")
	log.Printf("✅ Success: %d", success)
	log.Printf("❌ Failed: %d", failed)
	log.Println("🚀 Done")
}

func normalizeName(name string) string {
	name = strings.ReplaceAll(name, "/", "-")
	name = strings.ReplaceAll(name, "_", "-")
	name = strings.ToLower(name)

	// Azure max length = 127
	if len(name) > 127 {
		name = name[:127]
	}

	return name
}

func toPtr(s string) *string {
	return &s
}