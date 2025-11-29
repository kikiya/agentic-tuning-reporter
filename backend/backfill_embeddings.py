"""
Backfill embeddings for existing reports and findings.
Run this once to add embeddings to reports created before the similarity search feature.
"""

import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from database_sync import get_db
from models_sync import Report, Finding
from embedding_service import EmbeddingService

# Load environment variables from .env file
load_dotenv()

def backfill_report_embeddings(db: Session, embedding_service: EmbeddingService):
    """Generate embeddings for all reports that don't have them."""
    reports_without_embeddings = db.query(Report).filter(Report.embedding == None).all()
    
    print(f"Found {len(reports_without_embeddings)} reports without embeddings")
    
    for i, report in enumerate(reports_without_embeddings, 1):
        try:
            # Generate text representation
            text = f"{report.title}\n{report.description or ''}"
            if report.cluster_id:
                text += f"\nCluster: {report.cluster_id}"
            
            # Generate embedding
            embedding = embedding_service.embed_text(text)
            report.embedding = embedding
            
            print(f"[{i}/{len(reports_without_embeddings)}] Generated embedding for report: {report.title[:50]}...")
            
        except Exception as e:
            print(f"[ERROR] Failed to generate embedding for report {report.id}: {e}")
            continue
    
    # Commit all changes
    try:
        db.commit()
        print(f"\n✅ Successfully backfilled embeddings for {len(reports_without_embeddings)} reports")
    except Exception as e:
        db.rollback()
        print(f"\n❌ Failed to commit embeddings: {e}")

def backfill_finding_embeddings(db: Session, embedding_service: EmbeddingService):
    """Generate embeddings for all findings that don't have them."""
    findings_without_embeddings = db.query(Finding).filter(Finding.embedding == None).all()
    
    print(f"\nFound {len(findings_without_embeddings)} findings without embeddings")
    
    for i, finding in enumerate(findings_without_embeddings, 1):
        try:
            # Generate text representation
            text = f"{finding.title}\n{finding.description or ''}"
            text += f"\nCategory: {finding.category}\nSeverity: {finding.severity}"
            
            # Generate embedding
            embedding = embedding_service.embed_text(text)
            finding.embedding = embedding
            
            print(f"[{i}/{len(findings_without_embeddings)}] Generated embedding for finding: {finding.title[:50]}...")
            
        except Exception as e:
            print(f"[ERROR] Failed to generate embedding for finding {finding.id}: {e}")
            continue
    
    # Commit all changes
    try:
        db.commit()
        print(f"\n✅ Successfully backfilled embeddings for {len(findings_without_embeddings)} findings")
    except Exception as e:
        db.rollback()
        print(f"\n❌ Failed to commit embeddings: {e}")

def main():
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ ERROR: OPENAI_API_KEY environment variable not set")
        print("Please add OPENAI_API_KEY to backend/.env")
        return
    
    print("🚀 Starting embedding backfill...\n")
    
    # Initialize services
    embedding_service = EmbeddingService()
    db = next(get_db())
    
    try:
        # Backfill reports
        backfill_report_embeddings(db, embedding_service)
        
        # Backfill findings
        backfill_finding_embeddings(db, embedding_service)
        
        print("\n🎉 Backfill complete!")
        
    except Exception as e:
        print(f"\n❌ Backfill failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
