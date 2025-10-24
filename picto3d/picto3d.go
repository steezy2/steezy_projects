package main

import (
	"context"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"log/slog"
	"os"
	"strings"
	"sync"

	"github.com/google/generative-ai-go/genai"
	"google.golang.org/api/option"
)

// This is a placeholder for a 3D mesh structure.

// ShapeResolution defines the number of segments used for curved shapes like spheres and cylinders.
const ShapeResolution = 32

// A real implementation would use a library that provides
// data structures for vertices and faces.
type STLMesh struct {
	Name      string
	Triangles []Triangle
}

// A Triangle is defined by three vertices.
type Triangle struct {
	V1, V2, V3 [3]float32
}

// Scene represents the collection of geometric shapes described by Gemini.
type Scene struct {
	ID     string  `json:"id,omitempty" bson:"_id,omitempty"`
	Shapes []Shape `json:"shapes"`
}

// Shape defines a single geometric primitive in our scene.
type Shape struct {
	Type       string     `json:"type"`       // "cube", "sphere", "cylinder"
	Position   [3]float32 `json:"position"`   // Center of the shape [x, y, z]
	Rotation   [3]float32 `json:"rotation"`   // Euler angles in degrees [x, y, z]
	Dimensions [3]float32 `json:"dimensions"` // [width, height, depth] for a cube
	// Color      string     `json:"color"`      // Optional: e.g., "#FF0000"
}

func runImageToStlConversion(cfg *Config) error {
	// Step 1: The image will be loaded inside the conversion function.

	// Step 2: Convert the 2D image to a 3D mesh (The "Magic" happens here)
	scene, err := getSceneFromImage(cfg.InputImagePath)
	if err != nil {
		return fmt.Errorf("failed to get scene from image: %w", err)
	}

	// Step 3: Generate the mesh from the scene description
	mesh, err := generateMeshFromScene(*scene, cfg.Resolution)
	if err != nil {
		return fmt.Errorf("failed to generate mesh from scene: %w", err)
	}
	slog.Info("Successfully generated 3D mesh from image.")

	// Step 4: Save the 3D mesh as an STL file
	if err := saveStl(cfg.OutputStlPath, mesh); err != nil {
		return fmt.Errorf("failed to save STL file: %w", err)
	}
	slog.Info("Successfully saved STL file", "path", cfg.OutputStlPath)

	// Step 5: Save the generation record to the database
	if cfg.DBClient != nil {
		if err := saveSceneToDB(cfg.DBClient, *scene, cfg.InputImagePath); err != nil {
			// Log as a warning because the primary goal (file creation) succeeded.
			slog.Warn("Failed to save scene to database", "error", err)
		}
	}

	return nil
}

// convertImageTo3D orchestrates the two-step process of image-to-description and description-to-mesh.
func getSceneFromImage(imagePath string) (*Scene, error) {
	ctx := context.Background()
	apiKey := os.Getenv("GEMINI_API_KEY")
	if apiKey == "" {
		return nil, fmt.Errorf("you must set your 'GEMINI_API_KEY' environment variable")
	}

	// Step 2a: Create a new Gemini client
	client, err := genai.NewClient(ctx, option.WithAPIKey(apiKey))
	if err != nil {
		return nil, fmt.Errorf("failed to create gemini client: %w", err)
	}
	defer client.Close()

	// --- Step 2a: Get a text description of the image from Gemini ---
	imgData, err := os.ReadFile(imagePath)
	if err != nil {
		return nil, fmt.Errorf("failed to read image file: %w", err)
	}

	// Load the description prompt from file
	descriptionPromptBytes, err := os.ReadFile("prompts/1_describe_object.txt")
	if err != nil {
		return nil, fmt.Errorf("failed to read description prompt file: %w", err)
	}

	// Step 2c: Call the Gemini API with the image
	model := client.GenerativeModel("gemini-pro-vision")
	descriptionPrompt := []genai.Part{
		genai.ImageData("jpeg", imgData),
		genai.Text(descriptionPromptBytes),
	}

	slog.Info("Asking Gemini to describe the object for 3D modeling...")
	resp, err := model.GenerateContent(ctx, descriptionPrompt)
	if err != nil {
		return nil, fmt.Errorf("failed to generate content from gemini: %w", err)
	}

	// Step 2d: Process the response
	if len(resp.Candidates) == 0 || len(resp.Candidates[0].Content.Parts) == 0 {
		return nil, fmt.Errorf("received an empty response from Gemini")
	}
	description := resp.Candidates[0].Content.Parts[0]
	slog.Info("Gemini's Description", "description", description)

	// Load the JSON formatting prompt from file
	jsonPromptTemplate, err := os.ReadFile("prompts/2_format_json.txt")
	if err != nil {
		return nil, fmt.Errorf("failed to read json prompt file: %w", err)
	}

	// --- Step 2b: Ask Gemini to convert the description into structured JSON ---
	jsonPrompt := []genai.Part{
		genai.Text(fmt.Sprintf(string(jsonPromptTemplate), description)),
	}

	slog.Info("Asking Gemini to convert description to JSON...")
	// Use the text-only model for this part
	textModel := client.GenerativeModel("gemini-pro")
	jsonResp, err := textModel.GenerateContent(ctx, jsonPrompt...)
	if err != nil {
		return nil, fmt.Errorf("failed to generate JSON from gemini: %w", err)
	}
	if len(jsonResp.Candidates) == 0 || len(jsonResp.Candidates[0].Content.Parts) == 0 {
		return nil, fmt.Errorf("received an empty JSON response from Gemini")
	}

	// Clean up the JSON response from Gemini
	jsonText := strings.TrimSpace(fmt.Sprintf("%s", jsonResp.Candidates[0].Content.Parts[0]))
	jsonText = strings.TrimPrefix(jsonText, "```json")
	jsonText = strings.TrimPrefix(jsonText, "```")
	jsonText = strings.TrimSuffix(jsonText, "```")

	slog.Info("Gemini's JSON Output", "json", jsonText)

	// --- Step 2c: Parse the JSON and generate the mesh ---
	var scene Scene
	if err := json.Unmarshal([]byte(jsonText), &scene); err != nil {
		return nil, fmt.Errorf("failed to unmarshal scene JSON: %w", err)
	}

	return &scene, nil
}

// generateMeshFromScene converts the structured Scene object into an STLMesh.
func generateMeshFromScene(scene Scene, resolution int) (*STLMesh, error) {
	var wg sync.WaitGroup
	triangleChan := make(chan []Triangle, len(scene.Shapes))

	for _, shape := range scene.Shapes {
		wg.Add(1)
		go func(s Shape) {
			defer wg.Done()
			var triangles []Triangle
			switch s.Type {
			case "cube":
				slog.Info("Generating a cube", "dims", s.Dimensions, "pos", s.Position, "rot", s.Rotation)
				triangles = createCube(s.Position, s.Dimensions, s.Rotation)
			case "cylinder":
				slog.Info("Generating a cylinder", "dims", s.Dimensions, "pos", s.Position, "rot", s.Rotation)
				triangles = createCylinder(s.Position, s.Dimensions, s.Rotation, resolution)
			case "sphere":
				slog.Info("Generating a sphere", "dims", s.Dimensions, "pos", s.Position, "rot", s.Rotation)
				triangles = createSphere(s.Position, s.Dimensions[0]/2, s.Rotation, resolution, resolution)
			case "cone":
				slog.Info("Generating a cone", "dims", s.Dimensions, "pos", s.Position, "rot", s.Rotation)
				triangles = createCone(s.Position, s.Dimensions, s.Rotation, resolution)
			default:
				slog.Warn("Unknown shape type", "type", s.Type)
			}
			if len(triangles) > 0 {
				triangleChan <- triangles
			}
		}(shape)
	}

	// Wait for all goroutines to finish, then close the channel.
	go func() {
		wg.Wait()
		close(triangleChan)
	}()

	// Collect all the generated triangles into a single mesh.
	finalMesh := &STLMesh{Name: "GeneratedScene"}
	for tris := range triangleChan {
		finalMesh.Triangles = append(finalMesh.Triangles, tris...)
	}

	return finalMesh, nil
}

// saveStl writes the mesh to a binary STL file.
func saveStl(path string, mesh *STLMesh) error {
	file, err := os.Create(path)
	if err != nil {
		return fmt.Errorf("failed to create stl file: %w", err)
	}
	defer file.Close()

	// Write 80-byte header (can be empty)
	header := make([]byte, 80)
	if _, err := file.Write(header); err != nil {
		return fmt.Errorf("failed to write stl header: %w", err)
	}

	// Write number of triangles (uint32)
	numTriangles := uint32(len(mesh.Triangles))
	if err := binary.Write(file, binary.LittleEndian, numTriangles); err != nil {
		return fmt.Errorf("failed to write triangle count: %w", err)
	}

	// Write each triangle
	for _, tri := range mesh.Triangles {
		// Normal vector (3x float32)
		normal := calculateNormal(tri.V1, tri.V2, tri.V3)
		if err := binary.Write(file, binary.LittleEndian, normal); err != nil {
			return fmt.Errorf("failed to write normal: %w", err)
		}

		// Vertices (3x float32 each)
		if err := binary.Write(file, binary.LittleEndian, tri.V1); err != nil {
			return fmt.Errorf("failed to write vertex 1: %w", err)
		}
		if err := binary.Write(file, binary.LittleEndian, tri.V2); err != nil {
			return fmt.Errorf("failed to write vertex 2: %w", err)
		}
		if err := binary.Write(file, binary.LittleEndian, tri.V3); err != nil {
			return fmt.Errorf("failed to write vertex 3: %w", err)
		}

		// Attribute byte count (uint16), usually zero
		if err := binary.Write(file, binary.LittleEndian, uint16(0)); err != nil {
			return fmt.Errorf("failed to write attribute byte count: %w", err)
		}
	}

	return nil
}
