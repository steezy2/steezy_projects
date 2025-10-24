package main

import (
	"context"
	"fmt"
	"log/slog"
	"path/filepath"
	"time"

	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

// GenerationRecord is the structure we save to MongoDB.
type GenerationRecord struct {
	InputImageFile string    `bson:"inputImageFile"`
	GeneratedScene Scene     `bson:"generatedScene"`
	CreatedAt      time.Time `bson:"createdAt"`
}

func connectToDB(uri string) *mongo.Client {
	if uri == "" {
		slog.Warn("MONGODB_URI not set. Skipping database connection.")
		return nil
	}

	serverAPI := options.ServerAPI(options.ServerAPIVersion1)
	opts := options.Client().ApplyURI(uri).SetServerAPIOptions(serverAPI)
	// Create a context with a timeout
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	// Connect to MongoDB
	client, err := mongo.Connect(ctx, opts)
	if err != nil {
		slog.Error("Failed to connect to MongoDB", "error", err)
		return nil
	}

	// Ping the primary
	if err := client.Ping(ctx, nil); err != nil {
		slog.Error("Failed to ping MongoDB", "error", err)
		return nil
	}

	slog.Info("Successfully connected and pinged MongoDB!")
	return client
}

// saveSceneToDB saves the generation record to the MongoDB database.
func saveSceneToDB(client *mongo.Client, scene Scene, imagePath string) error {
	collection := client.Database("picto3d").Collection("generations")

	record := GenerationRecord{
		InputImageFile: filepath.Base(imagePath),
		GeneratedScene: scene,
		CreatedAt:      time.Now(),
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	result, err := collection.InsertOne(ctx, record)
	if err != nil {
		return fmt.Errorf("failed to insert record into mongo: %w", err)
	}

	slog.Info("Successfully saved generation record to database", "mongoID", result.InsertedID)
	return nil
}
