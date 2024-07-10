import os
import shutil

def organize_into_root(root_dir):
    def print_directory_structure(path, level=0):
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                print('│   ' * level + '├── ' + item)
                print_directory_structure(item_path, level + 1)
            else:
                print('│   ' * level + '├── ' + item)

    print("Original directory structure:")
    print(root_dir)


if __name__ == "__main__":
    organize_into_root("../../NeuralAnalyzer")
