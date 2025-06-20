from OpenGL.GL import *

def load_shader_from_file(path: str) -> str:
    with open(path, 'r') as file:
        return file.read()


class Shader():

    def __init__(self, source_path: str, shader_type: str):
        shader = glCreateShader(shader_type)
        glShaderSource(shader, load_shader_from_file(source_path))
        glCompileShader(shader)
        if not glGetShaderiv(shader, GL_COMPILE_STATUS):
            print("Shader program linking failed:")
            print(glGetShaderInfoLog(shader).decode())
        self._shader = shader

    @property
    def shader(self) -> int:
        return self._shader

    def release(self):
        glDeleteShader(self.shader)


class Program():

    def __init__(self, vertex_shader: Shader, fragment_shader: Shader):

        self._vertex_shader     = vertex_shader
        self._fragment_shader   = fragment_shader

        self._shader_program     = glCreateProgram()
        glAttachShader(self._shader_program, vertex_shader.shader)
        glAttachShader(self._shader_program, fragment_shader.shader)
        glLinkProgram(self._shader_program)

        # Check for linking errors
        if not glGetProgramiv(self._shader_program, GL_LINK_STATUS):
            print("Shader program linking failed:")
            print(glGetProgramInfoLog(self._shader_program).decode())

        """
        # Parint uniform IDs
        num_uniforms = glGetProgramiv(self._shader_program, GL_ACTIVE_UNIFORMS)
        print("Active uniforms:")
        for i in range(num_uniforms):
            name, size, type_ = glGetActiveUniform(self._shader_program, i)
            print(f"  {i}: {name}")
        """

    def use(self):
        glUseProgram(self._shader_program)

    def get_uniform_location(self, identifier: str) -> int:
        glUseProgram(self._shader_program)
        return glGetUniformLocation(self._shader_program, identifier)
    
    def release(self):
        self._vertex_shader.release()
        self._fragment_shader.release()
        glDeleteProgram(self._shader_program)