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

in vec3 vertex3;
in vec3 color3;
in vec4 color4;
in int  selection;

// out vec4  gl_Position;
// out float gl_PointSize;
out vec4 color;


void main() {
  gl_Position = pvmMatrix * vec4(vertex3, 1.0);
  gl_PointSize = pointSize.x;
  if (colors == 4) {
    color = color4;
  } else {
    color = vec4(color3, 1.0);
  }
}
