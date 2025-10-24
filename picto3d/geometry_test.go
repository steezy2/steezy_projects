package main

import (
	"testing"
)

func TestCreateCube(t *testing.T) {
	pos := [3]float32{0, 0, 0}
	dims := [3]float32{10, 10, 10}
	rot := [3]float32{0, 0, 0}

	triangles := createCube(pos, dims, rot)

	// A cube should always consist of 12 triangles (2 for each of its 6 faces).
	if len(triangles) != 12 {
		t.Errorf("Expected 12 triangles for a cube, but got %d", len(triangles))
	}
}
