/*

struct gl_DepthRangeParameters
{
    float near;
    float far;
    float diff;
};
uniform gl_DepthRangeParameters gl_DepthRange;

uniform int gl_NumSamples;

in vec4 gl_FragCoord;
in bool gl_FrontFacing;
in vec2 gl_PointCoord;

in int gl_SampleID;
in vec2 gl_SamplePosition;
in int gl_SampleMaskIn[];

in int gl_Layer;
in int gl_ViewportIndex;

out float gl_FragDepth;
out int gl_SampleMask[];

*/

#version 130

uniform sampler2D tex0;

uniform bool hasTexture = false;

uniform vec4 colorMask = vec4(1.0, 1.0, 1.0, 1.0);

in vec4 color;
in vec2 uv;

out vec4 fragment;

// out float gl_FragDepth;


void main() {
  vec4 value;

  if (hasTexture) {
    value = vec4(color.rgb + texture(tex0, uv).rgb, color.a);
  } else {
    value = color;
  }

  fragment = clamp(value * colorMask, 0.0, 1.0);

  gl_FragDepth = gl_FragCoord.z;
}
