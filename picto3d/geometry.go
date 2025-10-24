package main

import (
	"math"
)

// createCube generates 12 triangles for a cube with given position, dimensions, and rotation.
func createCube(pos, dims, rot [3]float32) []Triangle {
	// Define vertices around the origin (0,0,0)
	x0, x1 := -dims[0]/2, dims[0]/2
	y0, y1 := -dims[1]/2, dims[1]/2
	z0, z1 := -dims[2]/2, dims[2]/2

	v := [8][3]float32{
		{x0, y0, z0}, {x1, y0, z0}, {x1, y1, z0}, {x0, y1, z0},
		{x0, y0, z1}, {x1, y0, z1}, {x1, y1, z1}, {x0, y1, z1},
	}

	// Apply rotation and translation to each vertex
	for i := range v {
		v[i] = applyTransform(v[i], pos, rot)
	}

	// Create 12 triangles (2 for each of the 6 faces)
	return []Triangle{
		// Bottom face
		{v[0], v[1], v[2]}, {v[0], v[2], v[3]},
		// Top face
		{v[4], v[5], v[6]}, {v[4], v[6], v[7]},
		// Front face
		{v[0], v[4], v[7]}, {v[0], v[7], v[3]},
		// Back face
		{v[1], v[5], v[6]}, {v[1], v[6], v[2]},
		// Left face
		{v[0], v[4], v[5]}, {v[0], v[5], v[1]},
		// Right face
		{v[3], v[7], v[6]}, {v[3], v[6], v[2]},
	}
}

// createCylinder generates triangles for a cylinder.
// Dimensions are interpreted as [diameter, height, diameter].
func createCylinder(pos, dims, rot [3]float32, segments int) []Triangle {
	radius := dims[0] / 2
	height := dims[1]
	halfHeight := height / 2
	var triangles []Triangle

	// Define centers at origin
	bottomCenter := [3]float32{0, -halfHeight, 0}
	topCenter := [3]float32{0, halfHeight, 0}

	// Generate vertices for the top and bottom circles around the origin
	bottomVertices := make([][3]float32, segments)
	topVertices := make([][3]float32, segments)
	for i := 0; i < segments; i++ {
		angle := 2 * math.Pi * float64(i) / float64(segments)
		x := radius * float32(math.Cos(angle))
		z := radius * float32(math.Sin(angle))
		bottomVertices[i] = applyTransform([3]float32{x, -halfHeight, z}, pos, rot)
		topVertices[i] = applyTransform([3]float32{x, halfHeight, z}, pos, rot)
	}

	// Generate triangles for the walls, top cap, and bottom cap
	transformedBottomCenter := applyTransform(bottomCenter, pos, rot)
	transformedTopCenter := applyTransform(topCenter, pos, rot)
	for i := 0; i < segments; i++ {
		next_i := (i + 1) % segments

		// Bottom cap
		triangles = append(triangles, Triangle{transformedBottomCenter, bottomVertices[i], bottomVertices[next_i]})

		// Top cap
		triangles = append(triangles, Triangle{transformedTopCenter, topVertices[next_i], topVertices[i]})

		// Wall (two triangles to form a quad)
		triangles = append(triangles, Triangle{bottomVertices[i], topVertices[i], topVertices[next_i]})
		triangles = append(triangles, Triangle{bottomVertices[i], topVertices[next_i], bottomVertices[next_i]})
	}

	return triangles
}

// createSphere generates triangles for a sphere using UV mapping.
// Radius is the primary dimension. Stacks are latitude lines, sectors are longitude.
func createSphere(pos [3]float32, radius float32, rot [3]float32, stacks, sectors int) []Triangle {
	var triangles []Triangle
	vertices := make([][][3]float32, stacks+1)

	// Generate vertices around the origin
	for i := 0; i <= stacks; i++ {
		vertices[i] = make([][3]float32, sectors+1)
		stackAngle := math.Pi / 2 * (1 - 2*float64(i)/float64(stacks)) // From pi/2 to -pi/2
		xy := float64(radius) * math.Cos(stackAngle)
		y := float32(float64(radius) * math.Sin(stackAngle))

		for j := 0; j <= sectors; j++ {
			sectorAngle := 2 * math.Pi * float64(j) / float64(sectors)
			x := float32(xy * math.Cos(sectorAngle))
			z := float32(xy * math.Sin(sectorAngle))
			vertices[i][j] = applyTransform([3]float32{x, y, z}, pos, rot)
		}
	}

	// Generate triangles from vertices
	for i := 0; i < stacks; i++ {
		for j := 0; j < sectors; j++ {
			v1 := vertices[i][j]
			v2 := vertices[i+1][j]
			v3 := vertices[i+1][j+1]
			v4 := vertices[i][j+1]

			// Handle poles correctly
			if i != 0 {
				triangles = append(triangles, Triangle{v1, v2, v4})
			}
			if i != stacks-1 {
				triangles = append(triangles, Triangle{v2, v3, v4})
			}
		}
	}

	return triangles
}

// createCone generates triangles for a cone.
// Dimensions are [diameter, height, diameter].
func createCone(pos, dims, rot [3]float32, segments int) []Triangle {
	radius := dims[0] / 2
	height := dims[1]
	halfHeight := height / 2
	var triangles []Triangle

	// Define points at origin
	bottomCenter := [3]float32{0, -halfHeight, 0}
	tip := [3]float32{0, halfHeight, 0}

	// Generate vertices for the base circle
	bottomVertices := make([][3]float32, segments)
	for i := 0; i < segments; i++ {
		angle := 2 * math.Pi * float64(i) / float64(segments)
		x := radius * float32(math.Cos(angle))
		z := radius * float32(math.Sin(angle))
		bottomVertices[i] = applyTransform([3]float32{x, -halfHeight, z}, pos, rot)
	}

	// Generate triangles for the base and sides
	transformedBottomCenter := applyTransform(bottomCenter, pos, rot)
	transformedTip := applyTransform(tip, pos, rot)
	for i := 0; i < segments; i++ {
		next_i := (i + 1) % segments

		// Base triangle
		triangles = append(triangles, Triangle{transformedBottomCenter, bottomVertices[i], bottomVertices[next_i]})

		// Side triangle
		triangles = append(triangles, Triangle{transformedTip, bottomVertices[next_i], bottomVertices[i]})
	}

	return triangles
}

// applyTransform rotates and then translates a vertex.
func applyTransform(vertex, pos, rot [3]float32) [3]float32 {
	// Convert degrees to radians
	radX, radY, radZ := rot[0]*math.Pi/180, rot[1]*math.Pi/180, rot[2]*math.Pi/180

	// Pre-calculate sin/cos
	cosX, sinX := float32(math.Cos(float64(radX))), float32(math.Sin(float64(radX)))
	cosY, sinY := float32(math.Cos(float64(radY))), float32(math.Sin(float64(radY)))
	cosZ, sinZ := float32(math.Cos(float64(radZ))), float32(math.Sin(float64(radZ)))

	v := vertex

	// Apply rotation (Y, then X, then Z order - a common convention)
	// Rotate around Y axis
	v = [3]float32{v[0]*cosY + v[2]*sinY, v[1], -v[0]*sinY + v[2]*cosY}
	// Rotate around X axis
	v = [3]float32{v[0], v[1]*cosX - v[2]*sinX, v[1]*sinX + v[2]*cosX}
	// Rotate around Z axis
	v = [3]float32{v[0]*cosZ - v[1]*sinZ, v[0]*sinZ + v[1]*cosZ, v[2]}

	// Apply translation
	v[0] += pos[0]
	v[1] += pos[1]
	v[2] += pos[2]

	return v
}

// calculateNormal computes the normal vector for a triangle using the cross product.
func calculateNormal(v1, v2, v3 [3]float32) [3]float32 {
	// U = v2 - v1, V = v3 - v1
	u := [3]float32{v2[0] - v1[0], v2[1] - v1[1], v2[2] - v1[2]}
	v := [3]float32{v3[0] - v1[0], v3[1] - v1[1], v3[2] - v1[2]}

	// Cross product
	normal := [3]float32{
		u[1]*v[2] - u[2]*v[1],
		u[2]*v[0] - u[0]*v[2],
		u[0]*v[1] - u[1]*v[0],
	}

	// Normalize
	mag := float32(math.Sqrt(float64(normal[0]*normal[0] + normal[1]*normal[1] + normal[2]*normal[2])))
	if mag > 0 {
		normal[0] /= mag
		normal[1] /= mag
		normal[2] /= mag
	}

	return normal
}
