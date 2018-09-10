#version 130

in vec4 color;

out vec4 fragment;
// out float gl_FragDepth;


void main() {
  fragment = clamp(color, 0.0, 1.0);
}
