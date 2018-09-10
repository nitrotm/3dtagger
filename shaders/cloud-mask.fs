#version 130

in vec4 color;
in float dist;

out vec4 fragment;
// out float gl_FragDepth;


void main() {
  fragment = vec4(color.xyz * (1 - dist), 1.0);
}
