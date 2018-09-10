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
  vec4 bias, scale;

  gl_Position = pvmMatrix * vec4(vertex3, 1.0);
  if (selection != 0) {
    gl_PointSize = pointSize.x + 2.0;
    if (pictureOverlay) {
      bias = vec4(0.5, 0.5, 0.5, 0.0);
      scale = vec4(2.0, 2.0, 2.0, 1.0);
    } else {
      bias = vec4(0.5, 0.5, 1.0, 0.0);
      scale = vec4(0.5, 0.5, 1.0, 1.0);
    }
  } else {
    gl_PointSize = pointSize.x;
    if (pictureOverlay) {
      bias = vec4(0.0, 0.0, 0.0, 0.0);
      scale = vec4(0.25, 0.25, 0.25, 1.0);
    } else {
      bias = vec4(0.0, 0.0, 0.0, 0.0);
      scale = vec4(1.0, 1.0, 1.0, 1.0);
    }
  }
  if (pictureOverlay) {
    bias += vec4(0.5, 0.5, 0.5, 0.0);
  }
  if (colors == 4) {
    color = bias + scale * color4;
  } else {
    color = bias + scale * vec4(color3, 1.0);
  }
}
