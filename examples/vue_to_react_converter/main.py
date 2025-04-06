"""Main entry point for the Vue-to-React converter."""

import argparse
import asyncio
import os
import sys

from src import convert_vue_to_react


async def main():
    """Run the Vue-to-React converter."""
    parser = argparse.ArgumentParser(description="Convert Vue components to React components")
    parser.add_argument(
        "--source-dir",
        "-s",
        required=True,
        help="Directory containing Vue components",
    )
    parser.add_argument(
        "--destination-dir",
        "-d",
        required=True,
        help="Directory to write React components to",
    )
    parser.add_argument(
        "--batch-size",
        "-b",
        type=int,
        default=5,
        help="Maximum number of components to convert in a batch",
    )
    parser.add_argument(
        "--knowledge-base",
        "-k",
        help="Path to a knowledge base file",
    )
    parser.add_argument(
        "--max-fix-iterations",
        "-m",
        type=int,
        default=3,
        help="Maximum number of fix iterations to perform",
    )
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.source_dir):
        print(f"Error: Source directory '{args.source_dir}' does not exist")
        sys.exit(1)
    
    os.makedirs(args.destination_dir, exist_ok=True)
    
    if args.knowledge_base and not os.path.isfile(args.knowledge_base):
        print(f"Error: Knowledge base file '{args.knowledge_base}' does not exist")
        sys.exit(1)
    
    report = await convert_vue_to_react(
        source_dir=args.source_dir,
        destination_dir=args.destination_dir,
        batch_size=args.batch_size,
        knowledge_base_path=args.knowledge_base,
        max_fix_iterations=args.max_fix_iterations,
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
    
    print(f"\nDetailed report written to {os.path.join(args.destination_dir, 'docs', 'conversion_report.md')}")


if __name__ == "__main__":
    asyncio.run(main())
