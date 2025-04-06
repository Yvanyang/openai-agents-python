"""Example usage of the Vue-to-React converter."""

import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import convert_vue_to_react


async def main():
    """Run the Vue-to-React converter on the example Vue component."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    source_dir = script_dir
    destination_dir = os.path.join(script_dir, "output")
    
    knowledge_base_path = os.path.join(script_dir, "knowledge_base_example.json")
    
    print("Starting Vue to React conversion...")
    print(f"Source directory: {source_dir}")
    print(f"Destination directory: {destination_dir}")
    print(f"Knowledge base: {knowledge_base_path}")
    
    report = await convert_vue_to_react(
        source_dir=source_dir,
        destination_dir=destination_dir,
        batch_size=5,
        knowledge_base_path=knowledge_base_path,
        max_fix_iterations=3,
    )
    
    print("\nConversion Summary:")
    print(f"Total files: {report.total_files}")
    print(f"Successful conversions: {report.successful_conversions}")
    print(f"Partial conversions: {report.partial_conversions}")
    print(f"Failed conversions: {report.failed_conversions}")
    
    if report.attention_areas:
        print("\nAttention Areas:")
        for area in report.attention_areas:
            print(f"- {area['name']}: {len(area['components'])} components affected")
    
    print(f"\nDetailed report written to {os.path.join(destination_dir, 'docs', 'conversion_report.md')}")
    print(f"Converted components written to {os.path.join(destination_dir, 'components')}")


if __name__ == "__main__":
    asyncio.run(main())
