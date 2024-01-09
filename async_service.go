package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"math/rand"
	"net/http"
	"time"
)

type Payload struct {
	ID         int    `json:"id_order"`
	SessionKey string `json:"session_key"`
	// Add other fields if needed
}

func main() {
	http.HandleFunc("/deliver/", handlePost)
	http.ListenAndServe(":8080", nil)
}

func handlePost(w http.ResponseWriter, r *http.Request) {
	if r.Method == http.MethodPost {
		// Read the request body
		buf := new(bytes.Buffer)
		_, err := buf.ReadFrom(r.Body)
		if err != nil {
			logError(w, "Error reading request body", http.StatusInternalServerError)
			return
		}

		// Process the request body
		var payload Payload
		err = json.Unmarshal(buf.Bytes(), &payload)
		if err != nil {
			logError(w, "Error decoding JSON body", http.StatusBadRequest)
			return
		}

		// Access the ID and session key from the payload
		id := payload.ID
		sessionKey := payload.SessionKey

		fmt.Println("Received POST request with ID:", id)
		fmt.Println("Received POST request with SessionKey:", sessionKey)

		// Trigger the handleUpdateStatus function asynchronously
		go handleUpdateStatus(w, r, id, sessionKey)

		w.WriteHeader(http.StatusOK)
		w.Write([]byte("POST request processed successfully"))
	} else {
		logError(w, "Invalid request method", http.StatusMethodNotAllowed)
	}
}

func handleUpdateStatus(w http.ResponseWriter, r *http.Request, id int, sessionKey string) {
	// Simulate waiting for 5 seconds
	time.Sleep(5 * time.Second)

	// Generate a random boolean value (80% true, 20% false)
	isDelivered := rand.Float32() < 0.8

	// Prepare the JSON body with the randomly generated is_delivered value
	requestBody := map[string]bool{"is_delivered": isDelivered}
	jsonBody, err := json.Marshal(requestBody)
	if err != nil {
		logError(w, "Error encoding JSON body", http.StatusInternalServerError)
		return
	}

	// Perform a PUT request to another server with the ID and session key
	updateStatusURL := fmt.Sprintf("http://localhost:8000/api/order/%d/update/", id)
	req, err := http.NewRequest(http.MethodPut, updateStatusURL, bytes.NewBuffer(jsonBody))
	if err != nil {
		logError(w, "Error creating PUT request", http.StatusInternalServerError)
		return
	}

	// Set the session key in the headers
	req.Header.Set("Cookie", "session_key="+sessionKey)
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{}
	updateStatusResp, err := client.Do(req)
	if err != nil {
		logError(w, fmt.Sprintf("Error performing PUT request: %v", err), http.StatusInternalServerError)
		return
	}

	defer updateStatusResp.Body.Close()

	fmt.Println("PUT request to another server completed with status code:", updateStatusResp.Status)
}

func logError(w http.ResponseWriter, message string, statusCode int) {
	fmt.Println(message)
	http.Error(w, message, statusCode)
}
