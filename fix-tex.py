import os
import re
import argparse
from pathlib import Path
import shutil
from datetime import datetime

def process_math_content(content):
    """Process math content, replace < with \lt"""
    # Use regex to find all < and add appropriate spaces or braces before/after
    # Handle cases like ^{<N}
    content = re.sub(r'(\^{)<', r'\1\\lt ', content)
    content = re.sub(r'(\^)<', r'\1{\\lt ', content)
    # Ensure content after is wrapped in braces
    content = re.sub(r'<(\w+)', r'\\lt{\1}', content)
    # Handle other cases of <
    content = re.sub(r'<', r'\\lt ', content)
    return content

def process_markdown(content):
    """Process Markdown content, only replace < in math formulas"""
    
    # Store text parts during processing
    parts = []
    last_end = 0
    
    # Match all math formulas
    # Match patterns:
    # 1. $$...$$ (display math)
    # 2. $...$ (inline math)
    # 3. \[...\] (display math)
    # 4. \(...\) (inline math)
    pattern = r'(\$\$[\s\S]*?\$\$|\$[^\$\n]+\$|\\\[[^\]]*\\\]|\\\([^\)]*\\\))'
    
    for match in re.finditer(pattern, content):
        start, end = match.span()
        
        # Add regular text before math formula
        parts.append(content[last_end:start])
        
        # Process math formula
        math_content = match.group(1)
        if math_content.startswith('$$'):
            # Process display math
            processed = '$$' + process_math_content(math_content[2:-2]) + '$$'
        elif math_content.startswith('$'):
            # Process inline math
            processed = '$' + process_math_content(math_content[1:-1]) + '$'
        elif math_content.startswith('\\['):
            # Process \[...\] display math
            processed = '\\[' + process_math_content(math_content[2:-2]) + '\\]'
        else:
            # Process \(...\) inline math
            processed = '\\(' + process_math_content(math_content[2:-2]) + '\\)'
            
        parts.append(processed)
        last_end = end
    
    # Add remaining regular text
    parts.append(content[last_end:])
    
    return ''.join(parts)

def process_file(file_path, backup=True, dry_run=False):
    """Process a single file"""
    try:
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Process content
        processed_content = process_markdown(content)
        
        # Return if no changes needed
        if content == processed_content:
            return False, "No changes needed"
        
        if dry_run:
            return True, "Changes would be made (dry run)"
        
        # Create backup
        if backup:
            backup_path = str(file_path) + f'.bak.{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            shutil.copy2(file_path, backup_path)
        
        # Write processed content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(processed_content)
        
        return True, "Successfully processed"
        
    except Exception as e:
        return False, f"Error processing file: {str(e)}"

def process_directory(directory, backup=True, dry_run=False):
    """Process all Markdown files in directory"""
    results = []
    directory = Path(directory)
    
    for file_path in directory.rglob('*.md'):
        changed, message = process_file(file_path, backup, dry_run)
        results.append((file_path, changed, message))
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Process Markdown files to fix math formula notation')
    parser.add_argument('path', help='File or directory to process')
    parser.add_argument('--no-backup', action='store_true', help='Do not create backup files')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    args = parser.parse_args()
    
    path = Path(args.path)
    
    if path.is_file():
        # Process single file
        changed, message = process_file(path, not args.no_backup, args.dry_run)
        print(f"{path}: {'Would be changed' if args.dry_run else 'Changed' if changed else 'Unchanged'} - {message}")
    elif path.is_dir():
        # Process directory
        results = process_directory(path, not args.no_backup, args.dry_run)
        
        # Print statistics
        total = len(results)
        changed = sum(1 for _, c, _ in results if c)
        print(f"\nProcessing complete:")
        print(f"Total files: {total}")
        print(f"Files {'that would be changed' if args.dry_run else 'changed'}: {changed}")
        print(f"Files unchanged: {total - changed}")
        
        # Print detailed results
        if args.dry_run or changed > 0:
            print("\nDetailed results:")
            for file_path, changed, message in results:
                if changed or args.dry_run:
                    print(f"{file_path}: {message}")
    else:
        print(f"Error: {path} does not exist")

if __name__ == '__main__':
    main()