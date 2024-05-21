# Write file

def write_to_file(filename, content):
    with open(filename, 'w') as file:
        file.write(content)
    return filename


write_to_file_function = {
    "type": "function",
    "function": {
        "name": "write_to_file",
        "description": "Writes a given string into a file.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "The name of the file to write to",
                },
                "content": {
                    "type": "string",
                    "description": "The string to write into the file",
                }
            },
            "required": ["filename", "content"],
        },
    },
}

read_file_function = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "Opens and reads the given file.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "The name of the file to read from",
                },
            },
            "required": ["filename"],
        },
    },
}

class FileFunctions:
    def write_to_file(self, filename, content):
        with open(filename, 'w') as file:
           file.write(content)
        return filename
    
    def read_file(self, filename):
        with open(filename, 'r') as file:
            return file.read()
    
    def get_function_descriptions(self):
        return [write_to_file_function, read_file_function]
    