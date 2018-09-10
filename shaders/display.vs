/*

struct gl_DepthRangeParameters
{
    float near;
    float far;
    float diff;
};
uniform gl_DepthRangeParameters gl_DepthRange;

uniform int gl_NumSamples;

in int gl_VertexID;
in int gl_InstanceID;
in int gl_DrawID; // Requires GLSL 4.60 or ARB_shader_draw_parameters
in int gl_BaseVertex; // Requires GLSL 4.60 or ARB_shader_draw_parameters
in int gl_BaseInstance; // Requires GLSL 4.60 or ARB_shader_draw_parameters

out gl_PerVertex
{
  vec4 gl_Position;
  float gl_PointSize;
  float gl_ClipDistance[];
};

*/

#version 130

uniform mat4  pMatrix = mat4(
  1.0, 0.0, 0.0, 0.0,
  0.0, 1.0, 0.0, 0.0,
  0.0, 0.0, 1.0, 0.0,
  0.0, 0.0, 0.0, 1.0
);
uniform mat4  vMatrix = mat4(
  1.0, 0.0, 0.0, 0.0,
  0.0, 1.0, 0.0, 0.0,
  0.0, 0.0, 1.0, 0.0,
  0.0, 0.0, 0.0, 1.0
);
uniform mat4  mMatrix = mat4(
  1.0, 0.0, 0.0, 0.0,
  0.0, 1.0, 0.0, 0.0,
  0.0, 0.0, 1.0, 0.0,
  0.0, 0.0, 0.0, 1.0
);
uniform mat4  vmMatrix = mat4(
  1.0, 0.0, 0.0, 0.0,
  0.0, 1.0, 0.0, 0.0,
  0.0, 0.0, 1.0, 0.0,
  0.0, 0.0, 0.0, 1.0
);
uniform mat4  pvmMatrix = mat4(
  1.0, 0.0, 0.0, 0.0,
  0.0, 1.0, 0.0, 0.0,
  0.0, 0.0, 1.0, 0.0,
  0.0, 0.0, 0.0, 1.0
);

uniform int colors = 3;
uniform vec4 colorBias = vec4(0.0, 0.0, 0.0, 0.0);
uniform vec4 colorScale = vec4(1.0, 1.0, 1.0, 1.0);
uniform vec2 pointSize = vec2(1.0, 0.0);

in vec3 vertex3;
// in vec3 normal3;
in vec3 color3;
in vec4 color4;
in vec2 uv2;

// out vec4  gl_Position;
// out float gl_PointSize;
out vec4 color;
out vec2 uv;


void main() {
  gl_Position = pvmMatrix * vec4(vertex3, 1.0);
  gl_PointSize = pointSize.x;
  if (colors == 4) {
    color = color4 * colorScale + colorBias;
  } else {
    color = vec4(color3, 1.0) * colorScale + colorBias;
  }
  uv = uv2;
}
