package main

import (
	"context"
	"crypto/tls"
	"encoding/csv"
	"log"
	"net/http"
	"os"
	"time"

	vault "github.com/hashicorp/vault-client-go"
)

func main() {
	ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
	defer cancel()

	httpClient := &http.Client{
		Timeout: 30 * time.Second,
		Transport: &http.Transport{
			TLSClientConfig: &tls.Config{
				InsecureSkipVerify: true,
			},
		},
	}

	client, err := vault.New(
		vault.WithAddress("https://127.0.0.1:8200"),
		vault.WithHTTPClient(httpClient),
	)
	if err != nil {
		log.Fatal(err)
	}

	if err := client.SetToken("vault-root-token"); err != nil { //TODO: change this
		log.Fatal(err)
	}

	log.Println("Connected to Vault")

	file, err := os.Create("secrets.csv")
	if err != nil {
		log.Fatal(err)
	}
	defer file.Close()

	writer := csv.NewWriter(file)
	defer writer.Flush()

	writer.Write([]string{"path", "key", "value"})

	mountPath := "secret"
	fetchSecrets(ctx, client, mountPath, "", writer)

	log.Println("Secrets exported to secrets.csv")
}

func fetchSecrets(ctx context.Context, client *vault.Client, mountPath, currentPath string, writer *csv.Writer) {
	// ✅ FIX: use typed response
	resp, err := client.Secrets.KvV2List(ctx, currentPath, vault.WithMountPath(mountPath))
	if err != nil {
		log.Printf("Error listing path %s: %v", currentPath, err)
		return
	}

	// ✅ FIX: correct field
	for _, key := range resp.Data.Keys {

		// folder
		if key[len(key)-1] == '/' {
			fetchSecrets(ctx, client, mountPath, currentPath+key, writer)
			continue
		}

		fullPath := currentPath + key

		// ✅ FIX: typed read response
		secret, err := client.Secrets.KvV2Read(ctx, fullPath, vault.WithMountPath(mountPath))
		if err != nil {
			log.Printf("Error reading %s: %v", fullPath, err)
			continue
		}

		// ✅ FIX: correct field
		for k, v := range secret.Data.Data {
			writer.Write([]string{fullPath, k, toString(v)})
		}
	}
}

func toString(v interface{}) string {
	switch val := v.(type) {
	case string:
		return val
	default:
		return ""
	}
}
