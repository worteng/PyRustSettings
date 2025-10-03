import os

def print_directory_tree(startpath, indent=''):
    for item in sorted(os.listdir(startpath)):
        path = os.path.join(startpath, item)
        if os.path.isdir(path):
            print(f"{indent}📁 {item}/")
            print_directory_tree(path, indent + "  ")
        else:
            print(f"{indent}📄 {item}")

if __name__ == "__main__":
    project_root = "."  # Текущая папка
    print(f"Структура проекта ({os.path.abspath(project_root)}):")
    print_directory_tree(project_root)