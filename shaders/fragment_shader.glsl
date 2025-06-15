#version 330 core

in vec2 TexCoord;

out vec4 FragColor;

uniform sampler2D texture1;
uniform float alpha;

void main()
{
    FragColor = vec4(1.0, 1.0, 1.0, alpha) * texture(texture1, TexCoord);
}