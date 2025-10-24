package main

import (
	"context"
	"flag"
	"fmt"
	"log/slog"
	"os"

	"github.com/joho/godotenv"
	"go.mongodb.org/mongo-driver/mongo"
)

// Config holds all the configuration for the application.
type Config struct {
	InputImagePath string
	OutputStlPath  string
	Resolution     int
	DBClient       *mongo.Client
}

func main() {
	// Load environment variables from .env file
	if err := godotenv.Load(); err != nil {
		slog.Info("No .env file found, reading from environment")
	}

	// --- Parse configuration from command-line ---
	cfg, err := parseConfig()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		flag.Usage()
		os.Exit(1)
	}

	slog.Info("Starting PicTo3D conversion",
		"input", cfg.InputImagePath,
		"output", cfg.OutputStlPath,
		"resolution", cfg.Resolution,
	)

	// --- Establish and defer database connection ---
	cfg.DBClient = connectToDB(os.Getenv("MONGODB_URI"))
	if cfg.DBClient != nil {
		defer cfg.DBClient.Disconnect(context.Background())
	}

	// --- Run the main conversion logic ---
	if err := runImageToStlConversion(cfg); err != nil {
		slog.Error("Conversion process failed", "error", err)
		os.Exit(1)
	}
}

func parseConfig() (*Config, error) {
	cfg := &Config{}

	flag.IntVar(&cfg.Resolution, "res", 32, "Resolution for curved shapes (number of segments).")
	flag.Usage = func() {
		fmt.Fprintf(os.Stderr, "Usage: %s [-res <number>] <input_image.jpg> <output_model.stl>\n", os.Args[0])
		flag.PrintDefaults()
	}
	flag.Parse()

	args := flag.Args()
	if len(args) < 2 {
		return nil, fmt.Errorf("input image and output STL path are required")
	}
	cfg.InputImagePath = args[0]
	cfg.OutputStlPath = args[1]

	return cfg, nil
}
