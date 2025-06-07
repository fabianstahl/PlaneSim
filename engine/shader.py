from OpenGL.GL import *

def load_shader_from_file(path):
    with open(path, 'r') as file:
        return file.read()


class Shader():

    def __init__(self, source_path, shader_type):
        shader = glCreateShader(shader_type)
        glShaderSource(shader, load_shader_from_file(source_path))
        glCompileShader(shader)
        if not glGetShaderiv(shader, GL_COMPILE_STATUS):
            print("Shader program linking failed:")
            print(glGetShaderInfoLog(shader).decode())
        self.shader = shader

    def release(self):
        glDeleteShader(self.shader)


class Program():

    def __init__(self, vertex_shader, fragment_shader):

        self.vertex_shader      = vertex_shader
        self.fragment_shader    = fragment_shader

        self.shader_program     = glCreateProgram()
        glAttachShader(self.shader_program, vertex_shader.shader)
        glAttachShader(self.shader_program, fragment_shader.shader)
        glLinkProgram(self.shader_program)

        # Check for linking errors
        if not glGetProgramiv(self.shader_program, GL_LINK_STATUS):
            print("Shader program linking failed:")
            print(glGetProgramInfoLog(self.shader_program).decode())

        """
        # Parint uniform IDs
        num_uniforms = glGetProgramiv(self.shader_program, GL_ACTIVE_UNIFORMS)
        print("Active uniforms:")
        for i in range(num_uniforms):
            name, size, type_ = glGetActiveUniform(self.shader_program, i)
            print(f"  {i}: {name}")
        """

    def use(self):
        glUseProgram(self.shader_program)

    def get_uniform_location(self, identifier):
        glUseProgram(self.shader_program)
        return glGetUniformLocation(self.shader_program, identifier)
    
    def release(self):
        self.vertex_shader.release()
        self.fragment_shader.release()
        glDeleteProgram(self.shader_program)