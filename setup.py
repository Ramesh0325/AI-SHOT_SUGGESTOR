import os

def create_directory_structure():
    """Create the directory structure for the application"""
    # Create main directories
    directories = [
        "pages",
        "static/images",
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        
    print("Directory structure created successfully!")

if __name__ == "__main__":
    create_directory_structure()