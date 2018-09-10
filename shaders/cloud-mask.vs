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
uniform vec2 pointSize = vec2(1.0, 0.0);
uniform bool pictureOverlay = false;

uniform vec3 cameraPosition = vec3(0.0, 0.0, 0.0);
uniform vec2 maskPointSize = vec2(1.0, 0.0);
uniform vec2 maskDistanceRange = vec2(0.0, 1.0);

in vec3 vertex3;
in int  selection;

// out vec4  gl_Position;
// out float gl_PointSize;
out vec4 color;
out float dist;


void main() {
  vec4 vertex = vec4(vertex3, 1.0);
  float d = distance((mMatrix * vertex).xyz, cameraPosition);

  gl_Position = pvmMatrix * vertex;
  if (selection != 0) {
    gl_PointSize = maskPointSize.x;
    color = vec4(1.0, 1.0, 1.0, 1.0);
  } else {
    gl_PointSize = 2.0;
    color = vec4(0.0, 0.0, 0.0, 0.0);
  }
  dist = (d - maskDistanceRange.x) / (maskDistanceRange.y - maskDistanceRange.x);
}
