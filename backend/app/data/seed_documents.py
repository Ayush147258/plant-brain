import asyncio
import logging
from app.core.document_store import upload_document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_documents")

DOCUMENTS = [
    {
        "filename": "Centrifugal Pump P-201 Maintenance Manual",
        "content": "P-201 Centrifugal Pump Specifications: Flow rate 500 m3/h, Head 120m, Speed 2950 RPM. Maintenance Intervals: Check bearing oil level weekly. Replace mechanical seal every 8000 hours. Common Failure Modes: Cavitation due to low NPSHA, indicated by crackling noise. Bearing failure indicated by vibration exceeding 4.5 mm/s. Actions: If vibration exceeds limits, check alignment and balance. For seal wear, check flush liquid pressure.",
        "source_type": "manual",
        "metadata": {
            "page_or_section": "Section 4.1",
            "freshness_score": 0.95,
            "last_validated_date": "2023-10-15",
            "equipment_tags": ["P-201", "Pump", "Centrifugal"]
        }
    },
    {
        "filename": "Compressor C-101 Operator Guide",
        "content": "C-101 Reciprocating Compressor. Capacity: 2500 Nm3/h. Discharge Pressure: 45 bar. Routine checks: Inspect cylinder lube oil system daily. Monitor interstage pressures and temperatures. Common Issues: Valve failure leads to high interstage temperature and low capacity. Piston ring wear causes blowby. If discharge temp exceeds 150C, shut down immediately and inspect valves.",
        "source_type": "manual",
        "metadata": {
            "page_or_section": "Section 2.2",
            "freshness_score": 0.80,
            "last_validated_date": "2022-05-20",
            "equipment_tags": ["C-101", "Compressor"]
        }
    },
    {
        "filename": "Heat Exchanger E-105 Manual",
        "content": "E-105 Shell and Tube Heat Exchanger. Surface area: 150 m2. Tubes: Carbon steel, 19mm OD. Shell side: Cooling water. Tube side: Process gas. Maintenance: Clean tubes every 2 years or when pressure drop exceeds 0.5 bar. Tube leak detection by analyzing cooling water for process gas. Fouling reduces heat transfer coefficient significantly. Descaling procedure involves circulating 5% inhibited HCl solution.",
        "source_type": "manual",
        "metadata": {
            "page_or_section": "Section 3.4",
            "freshness_score": 0.70,
            "last_validated_date": "2021-11-10",
            "equipment_tags": ["E-105", "Heat Exchanger"]
        }
    },
    {
        "filename": "OISD-116 Fire Protection Facilities",
        "content": "OISD-116: Fire Protection Facilities for Petroleum Refineries and Oil/Gas Processing Plants. Section 5.1: Hydrant network shall be provided covering all areas. Pressure at the hydraulically most remote point shall not be less than 7 kg/cm2. Section 6.2: Fixed water spray systems shall be provided for equipment containing flammable liquids. Testing frequency: Fire water pumps weekly, hydrant valves monthly. Deviation from these testing intervals is a major non-compliance.",
        "source_type": "regulation",
        "metadata": {
            "page_or_section": "Sections 5.1, 6.2",
            "freshness_score": 0.90,
            "last_validated_date": "2023-08-01",
            "equipment_tags": ["Fire System", "Hydrant"]
        }
    },
    {
        "filename": "Factory Act Excerpt - Section 41",
        "content": "Factory Act, 1948 - Section 41: Safety Officers. In every factory wherein one thousand or more workers are ordinarily employed, or wherein any manufacturing process or operation is carried on, which process or operation involves any risk of bodily injury, poisoning or disease, or any other hazard to health, the occupier shall, if so required by the State Government, appoint such number of Safety Officers. Must conduct safety audits every 6 months.",
        "source_type": "regulation",
        "metadata": {
            "page_or_section": "Section 41",
            "freshness_score": 1.0,
            "last_validated_date": "2024-01-10",
            "equipment_tags": ["Safety", "Compliance"]
        }
    },
    {
        "filename": "Work Order WO-2023-8921",
        "content": "Work Order WO-2023-8921. Equipment: P-201. Date: 2023-11-05. Technician: Rajesh Kumar. Observation: High vibration (5.2 mm/s) on inboard bearing. Crackling noise indicating possible cavitation. Actions Taken: Stopped pump. Checked alignment, found within tolerance. Replaced inboard bearing due to noticeable wear. Checked suction strainer, found partially clogged. Cleaned strainer. Restarted pump, vibration normal (1.8 mm/s).",
        "source_type": "work_order",
        "metadata": {
            "page_or_section": "Page 1",
            "freshness_score": 0.85,
            "last_validated_date": "2023-11-06",
            "equipment_tags": ["P-201", "Pump", "Vibration"]
        }
    },
    {
        "filename": "Work Order WO-2023-9044",
        "content": "Work Order WO-2023-9044. Equipment: C-101. Date: 2023-12-12. Technician: Amit Singh. Observation: High interstage temperature (155C) between 1st and 2nd stage. Actions Taken: Shut down compressor. Inspected 1st stage discharge valves. Found broken valve plate. Replaced valve assembly. Checked piston rings, found acceptable. Restarted compressor, temperature stabilized at 135C.",
        "source_type": "work_order",
        "metadata": {
            "page_or_section": "Page 1",
            "freshness_score": 0.90,
            "last_validated_date": "2023-12-13",
            "equipment_tags": ["C-101", "Compressor", "Valve"]
        }
    },
    {
        "filename": "Work Order WO-2022-4511",
        "content": "Work Order WO-2022-4511. Equipment: E-105. Date: 2022-08-20. Technician: Suresh Verma. Observation: High pressure drop across tube side (0.7 bar). Actions Taken: Isolated E-105. Opened tube bundles. Significant fouling observed. Performed hydro-jetting. Pressure drop after cleaning: 0.2 bar. Note: Consider increasing cooling water treatment chemicals.",
        "source_type": "work_order",
        "metadata": {
            "page_or_section": "Page 1",
            "freshness_score": 0.40,
            "last_validated_date": "2022-08-21",
            "equipment_tags": ["E-105", "Heat Exchanger", "Fouling"]
        }
    },
    {
        "filename": "Inspection Report IR-2023-11",
        "content": "Annual Inspection Report for Zone 3. Equipment Checked: P-201, HX-204, V-102. Findings: P-201 seal shows minor weeping, monitor. HX-204 shell shows signs of external corrosion under insulation (CUI). V-102 relief valve calibration expired. Urgent Action: HX-204 requires thickness measurement. Note: HX-204 shares process line with P-201. Due to inspection delay, HX-204 is overdue by 12 days.",
        "source_type": "inspection",
        "metadata": {
            "page_or_section": "Summary",
            "freshness_score": 0.95,
            "last_validated_date": "2023-12-01",
            "equipment_tags": ["P-201", "HX-204", "V-102", "Zone 3"]
        }
    },
    {
        "filename": "Inspection Report IR-2022-04",
        "content": "Vibration Analysis Report. Equipment: C-101. Date: 2022-04-15. Baseline vibration: 2.1 mm/s. Current vibration: 3.8 mm/s. Spectrum analysis indicates 1X RPM dominant peak, suggesting unbalance. Recommendation: Perform dynamic balancing of flywheel during next turnaround. Monitor bi-weekly until then.",
        "source_type": "inspection",
        "metadata": {
            "page_or_section": "Page 2",
            "freshness_score": 0.50,
            "last_validated_date": "2022-04-16",
            "equipment_tags": ["C-101", "Vibration"]
        }
    },
    {
        "filename": "Confined Space Entry Procedure",
        "content": "SOP-05: Confined Space Entry. 1. Isolate all energy sources (LOTO). 2. Purge space with inert gas, then ventilate with fresh air for minimum 4 hours. 3. Test atmosphere: Oxygen must be 19.5% - 23.5%. LEL must be < 5%. H2S must be < 10 ppm. 4. Obtain valid permit signed by Shift In-Charge. 5. Assign a standby person (hole watch) who remains outside constantly.",
        "source_type": "procedure",
        "metadata": {
            "page_or_section": "Steps 1-5",
            "freshness_score": 0.98,
            "last_validated_date": "2024-02-01",
            "equipment_tags": ["Safety", "Confined Space"]
        }
    },
    {
        "filename": "Hot Work Permit Procedure",
        "content": "SOP-12: Hot Work Permit. Applies to welding, cutting, grinding. Preparation: Remove combustible materials within 10 meters. Cover drains. Keep two 9kg DCP fire extinguishers at site. Atmospheric testing for LEL is mandatory before starting. A dedicated fire watch must be present during work and 30 minutes after completion.",
        "source_type": "procedure",
        "metadata": {
            "page_or_section": "Section 2",
            "freshness_score": 0.90,
            "last_validated_date": "2023-09-15",
            "equipment_tags": ["Safety", "Hot Work"]
        }
    },
    {
        "filename": "Incident Report INC-2023-08",
        "content": "Incident INC-2023-08. Date: 2023-08-10. Location: Unit 2. Event: Seal failure on pump P-201 leading to minor spill of naphtha. Investigation: Operator noticed pool of liquid under pump. Plant shut down safely. Root Cause: Wrong seal material used during last maintenance (WO-2023-4412). Nitrile used instead of Viton, leading to chemical degradation. Corrective Action: Update BOM in ERP to specify Viton only. Conduct training on material compatibility.",
        "source_type": "incident",
        "metadata": {
            "page_or_section": "Executive Summary",
            "freshness_score": 0.95,
            "last_validated_date": "2023-08-25",
            "equipment_tags": ["P-201", "Spill", "Seal"]
        }
    }
]

async def main():
    logger.info("Starting seed process for PlantBrain documents...")
    
    success_count = 0
    for doc in DOCUMENTS:
        try:
            await upload_document(
                filename=doc["filename"],
                content=doc["content"],
                source_type=doc["source_type"],
                metadata=doc["metadata"]
            )
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to seed {doc['filename']}: {e}")
            
    logger.info(f"Seed process complete. Successfully uploaded {success_count}/{len(DOCUMENTS)} documents.")

if __name__ == "__main__":
    asyncio.run(main())
