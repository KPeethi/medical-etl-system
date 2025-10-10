"""
Dataset1_ClassicExcelMap Processing Script
Comprehensive medical ETL processing with Excel mapping support
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add modules to path
sys.path.append(str(Path(__file__).parent / "modules"))
sys.path.append(str(Path(__file__).parent / "config"))

def process_dataset1_classicexcelmap(dataset_path=None, output_path=None, mapping_file=None):
    """
    Process Dataset1_ClassicExcelMap using the medical ETL system
    """
    
    print("=" * 60)
    print("DATASET1_CLASSICEXCELMAP PROCESSING")
    print("=" * 60)
    
    # Use provided paths or defaults
    if dataset_path is None:
        dataset_path = Path.cwd() / "Dataset1_ClassicExcelMap"
    else:
        dataset_path = Path(dataset_path)
        
    if output_path is None:
        output_path = Path.cwd() / "processed_datasets" / "Dataset1_Output"
    else:
        output_path = Path(output_path)
        
    if mapping_file is None:
        mapping_file = Path("data/Patient_Mapping_Template.xlsx")
    else:
        mapping_file = Path(mapping_file)
    
    print(f"Dataset Source: {dataset_path}")
    print(f"Output Destination: {output_path}")
    print(f"Mapping File: {mapping_file}")
    print()
    
    # Check if dataset exists
    if not dataset_path.exists():
        print("❌ ERROR: Dataset path not found!")
        print(f"Expected location: {dataset_path}")
        print()
        print("📋 SOLUTION OPTIONS:")
        print("1. Copy Dataset1_ClassicExcelMap to the expected location")
        print("2. Update the dataset_path in this script")
        print("3. Create a symbolic link to the dataset")
        print()
        return False
    
    # Check if mapping file exists
    if not mapping_file.exists():
        print("❌ WARNING: Mapping file not found!")
        print(f"Expected location: {mapping_file}")
        print()
        print("🔧 Creating Excel mapping template...")
        create_mapping_template()
    
    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Import and run ETL system
    try:
        from main import MedicalETLProcessor
        
        print("🚀 Starting Medical ETL Processing...")
        print()
        
        # Initialize ETL processor
        processor = MedicalETLProcessor(
            source_path=dataset_path,
            destination_path=output_path,
            mapping_file=mapping_file if mapping_file.exists() else None,
            dry_run=False  # Set to True for testing
        )
        
        # Run the ETL process
        results = processor.run()
        
        # Display results
        display_processing_results(results)
        
        return True
        
    except ImportError as e:
        print(f"❌ ERROR: Unable to import ETL system: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR: Processing failed: {e}")
        return False

def create_mapping_template():
    """Create Excel mapping template if it doesn't exist"""
    try:
        from modules.excel_manager import ExcelManager
        
        excel_manager = ExcelManager()
        mapping_file = Path("data/Patient_Mapping_Template.xlsx")
        
        # Create data directory if it doesn't exist
        mapping_file.parent.mkdir(exist_ok=True)
        
        # Create the mapping template
        success = excel_manager.create_mapping_template(str(mapping_file))
        
        if success:
            print("✅ Excel mapping template created successfully!")
            print(f"📄 Template saved to: {mapping_file}")
        else:
            print("❌ Failed to create Excel mapping template")
            
    except Exception as e:
        print(f"❌ ERROR creating mapping template: {e}")

def display_processing_results(results):
    """Display comprehensive processing results"""
    
    print("=" * 60)
    print("PROCESSING RESULTS")
    print("=" * 60)
    
    # Session information
    if 'session_info' in results:
        session = results['session_info']
        print(f"📋 Session ID: {session.get('session_id', 'N/A')}")
        print(f"🕐 Start Time: {session.get('start_time', 'N/A')}")
        print(f"📂 Source: {session.get('source_path', 'N/A')}")
        print(f"📁 Destination: {session.get('destination_path', 'N/A')}")
        print()
    
    # Processing summary
    if 'processing_summary' in results:
        summary = results['processing_summary']
        print("📊 PROCESSING SUMMARY:")
        print(f"   Total Files Found: {summary.get('total_files_found', 0)}")
        print(f"   Files Processed: {summary.get('total_files_processed', 0)}")
        print(f"   Successful Extractions: {summary.get('successful_extractions', 0)}")
        print(f"   Failed Extractions: {summary.get('failed_extractions', 0)}")
        print(f"   Mapped Files: {summary.get('mapped_files', 0)}")
        print(f"   Unmapped Files: {summary.get('unmapped_files', 0)}")
        print(f"   Duplicate Files: {summary.get('duplicate_files', 0)}")
        print(f"   Organized Files: {summary.get('organized_files', 0)}")
        print(f"   Unique Patients: {summary.get('unique_patients', 0)}")
        print()
        
        # File size information
        total_source = summary.get('total_source_size_mb', 0)
        total_dest = summary.get('total_destination_size_mb', 0)
        print(f"💾 FILE SIZES:")
        print(f"   Total Source Size: {total_source:.2f} MB")
        print(f"   Total Destination Size: {total_dest:.2f} MB")
        print()
        
        # Processing methods
        methods = summary.get('processing_methods', {})
        if methods:
            print(f"🔍 PROCESSING METHODS USED:")
            for method, count in methods.items():
                print(f"   {method}: {count} files")
            print()
    
    # Error information
    errors = results.get('processing_summary', {}).get('errors', [])
    if errors:
        print(f"❌ ERRORS ({len(errors)}):")
        for error in errors[:5]:  # Show first 5 errors
            print(f"   • {error}")
        if len(errors) > 5:
            print(f"   ... and {len(errors) - 5} more errors")
        print()
    
    # Log file information
    log_file = results.get('session_info', {}).get('log_file')
    if log_file:
        print(f"📄 Log File: {log_file}")
        try:
            log_path = Path(log_file)
            if log_path.exists():
                log_size = log_path.stat().st_size / 1024  # KB
                print(f"📏 Log Size: {log_size:.1f} KB")
        except:
            pass
        print()

def demo_without_dataset():
    """Run a demonstration without the actual dataset"""
    
    print("=" * 60)
    print("DEMO MODE - DATASET1_CLASSICEXCELMAP SIMULATION")
    print("=" * 60)
    
    # Create a demo mapping file
    demo_mapping = Path("data/Demo_Dataset1_Mapping.xlsx")
    
    try:
        from modules.excel_manager import ExcelManager
        
        excel_manager = ExcelManager()
        
        # Create demo mapping template
        demo_mapping.parent.mkdir(exist_ok=True)
        success = excel_manager.create_mapping_template(str(demo_mapping))
        
        if success:
            print("✅ Demo mapping template created!")
            print(f"📄 Location: {demo_mapping}")
            print()
            
            # Show what the system would do
            print("🔍 EXPECTED PROCESSING WORKFLOW:")
            print("1. 📂 Scan Dataset1_ClassicExcelMap directory")
            print("2. 🗜️  Extract any archive files (ZIP, RAR, 7Z)")
            print("3. 📋 Load Excel mapping file for patient data")
            print("4. 📄 Process each medical file (PDF, images)")
            print("5. 🔍 Extract patient information using:")
            print("   - Excel mapping lookup (primary)")
            print("   - Filename parsing (secondary)")
            print("   - OCR text extraction (tertiary)")
            print("   - Deep PDF scanning (fallback)")
            print("6. 🗂️  Organize files by patient folders")
            print("7. 📊 Generate comprehensive logs")
            print("8. 📈 Export results to Excel")
            print()
            
            print("📋 LOG FILE CONTENTS WILL INCLUDE:")
            print("• Source and destination paths for each file")
            print("• File sizes in MB")
            print("• Patient file counts")
            print("• Processing methods used")
            print("• Skipped files with reasons")
            print("• Complete audit trail")
            print("• Patient-level summaries")
            print("• Session statistics")
            print()
            
            return True
            
    except Exception as e:
        print(f"❌ Demo setup failed: {e}")
        return False

def main():
    """Main execution function"""
    
    parser = argparse.ArgumentParser(
        description="Process Dataset1_ClassicExcelMap with medical ETL system"
    )
    parser.add_argument(
        "--dataset-path", 
        type=str,
        help="Path to Dataset1_ClassicExcelMap directory"
    )
    parser.add_argument(
        "--output-path",
        type=str, 
        help="Output directory for processed files"
    )
    parser.add_argument(
        "--mapping-file",
        type=str,
        help="Excel mapping file path"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run in demo mode without actual dataset"
    )
    
    args = parser.parse_args()
    
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    if args.demo:
        # Run demo mode
        print("ℹ️  Running in demo mode...")
        print()
        success = demo_without_dataset()
    else:
        # Determine dataset path
        if args.dataset_path:
            dataset_path = Path(args.dataset_path)
        else:
            # Try common locations
            possible_paths = [
                Path.cwd() / "Dataset1_ClassicExcelMap",
                Path.home() / "Downloads" / "Dataset1_ClassicExcelMap",
                Path("Dataset1_ClassicExcelMap")
            ]
            
            dataset_path = None
            for path in possible_paths:
                if path.exists():
                    dataset_path = path
                    break
            
            if dataset_path is None:
                print("❌ Dataset not found in common locations:")
                for path in possible_paths:
                    print(f"   • {path}")
                print()
                print("💡 Use --dataset-path to specify custom location")
                print("💡 Use --demo to run without dataset")
                return False
        
        # Process actual dataset
        success = process_dataset1_classicexcelmap(
            dataset_path=args.dataset_path,
            output_path=args.output_path,
            mapping_file=args.mapping_file
        )
    
    if success:
        print("🎉 Processing completed successfully!")
    else:
        print("❌ Processing failed. Check the output above for details.")
    
    print()
    print(f"🕐 Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return success


if __name__ == "__main__":
    main()