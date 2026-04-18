"""Mailing pack generation services."""
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path
from jinja2 import Template
import uuid
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from ..core.logging import logger
from ..core.errors import MailingPackError
from ..utils import ensure_output_dir, save_file


class MailingPackGenerator:
    """Generates mailing packs for prospects."""

    PROSPECT_EMAIL_TEMPLATE = """Subject: Solar Savings Opportunity for {{business_name}}

Hi {{recipient_name}},

We identified your property at {{address}} as a strong candidate for rooftop solar.

Based on available roof area, your site may support approximately {{panel_count}} panels with meaningful annual electricity savings.

We prepared a visual concept for your property.

Would you be open to a short discussion?

Regards,
Solarware
"""

    @staticmethod
    def _opportunity_tier(suitability_score: int) -> str:
        if suitability_score >= 80:
            return "High"
        if suitability_score >= 60:
            return "Medium"
        return "Early-stage"

    @staticmethod
    def generate_outreach_content(prospect: Dict, suitability_score: int) -> Dict[str, str]:
        """Create concise multi-channel outreach copy for the same lead."""
        business_name = prospect.get("business_name") or "your business"
        address = prospect.get("address") or "your property"
        roof_area_sqm = float(prospect.get("roof_area_sqm") or 0)
        roof_area_sqft = int(round(roof_area_sqm * 10.7639))
        tier = MailingPackGenerator._opportunity_tier(suitability_score)

        cold_email = (
            f"Subject: Rooftop solar opportunity for {business_name}\n\n"
            f"Hi there,\n\n"
            f"We reviewed {address} and found rooftop conditions consistent with a {tier.lower()}-priority solar lead. "
            f"The roof footprint (~{roof_area_sqft:,} sqft) appears suitable for a commercial layout and staged rollout.\n\n"
            f"If useful, we can share a short feasibility walkthrough and before/after roof concept this week.\n\n"
            f"Best,\nSolarware Team"
        )

        whatsapp_intro = (
            f"Hi, we assessed {address} for commercial rooftop solar. "
            f"It scores {suitability_score}/100 ({tier} tier) and looks suitable for a short feasibility call. "
            f"Can I share the roof concept image?"
        )

        follow_up_text = (
            f"Quick follow-up on {business_name}: we have your rooftop concept ready and can walk through practical next steps in 15 minutes."
        )

        return {
            "cold_email": cold_email,
            "whatsapp_intro": whatsapp_intro,
            "follow_up_text": follow_up_text,
        }

    @staticmethod
    def generate(
        prospect: Dict,
        contact: Optional[Dict] = None,
        satellite_image_path: Optional[str] = None,
        mockup_image_path: Optional[str] = None,
        before_after_image_path: Optional[str] = None,
    ) -> Dict:
        """Generate mailing pack for a prospect.
        
        Args:
            prospect: Prospect data
            contact: Contact information
            satellite_image_path: Path to satellite image
            mockup_image_path: Path to mockup image
        
        Returns:
            Dictionary with mailing pack information
        
        Raises:
            MailingPackError: If generation fails
        """
        try:
            logger.info(f"Generating mailing pack for {prospect.get('address')}")
            
            # Prepare template variables
            contact = contact or {}
            recipient_name = contact.get("contact_name") or "there"

            suitability_score = int(prospect.get("solar_score") or 0)
            opportunity_tier = MailingPackGenerator._opportunity_tier(suitability_score)

            email_subject = f"Solar Savings Opportunity for {prospect.get('business_name') or 'Your Property'}"

            # Render email
            template = Template(MailingPackGenerator.PROSPECT_EMAIL_TEMPLATE)
            email_body = template.render(
                recipient_name=recipient_name,
                business_name=prospect.get("business_name", "your business"),
                address=prospect.get("address", "Unknown Address"),
                panel_count=prospect.get("estimated_panel_count", 0),
            )
            
            # Create mailing pack directory
            pack_id = str(uuid.uuid4())
            pack_dir = ensure_output_dir(f"mailing_packs/{pack_id}")
            
            # Save email content
            email_filename = f"email_{pack_id}.txt"
            email_path = pack_dir / email_filename
            with open(email_path, "w") as f:
                f.write(email_body)

            pdf_filename = f"mail_pack_{pack_id}.pdf"
            pdf_path = pack_dir / pdf_filename
            MailingPackGenerator._generate_pdf(
                pdf_path=pdf_path,
                prospect=prospect,
                contact=contact,
                email_subject=email_subject,
                email_body=email_body,
                before_image_path=satellite_image_path,
                after_image_path=mockup_image_path,
            )
            
            outreach_content = MailingPackGenerator.generate_outreach_content(
                prospect=prospect,
                suitability_score=suitability_score,
            )

            # Create manifest
            manifest = {
                "id": pack_id,
                "prospect_id": str(prospect.get("id", "unknown")),
                "address": prospect.get("address"),
                "business_name": prospect.get("business_name"),
                "contact_email": contact.get("email"),
                "contact_phone": contact.get("phone"),
                "email_subject": email_subject,
                "email_body": email_body,
                "email_path": str(email_path),
                "pdf_path": str(pdf_path),
                "satellite_image_path": satellite_image_path,
                "mockup_image_path": mockup_image_path,
                "before_after_image_path": before_after_image_path,
                "system_capacity_kw": prospect.get("estimated_system_capacity_kw"),
                "suitability_score": suitability_score,
                "opportunity_tier": opportunity_tier,
                "outreach": outreach_content,
                "created_at": datetime.utcnow().isoformat(),
                "status": "prepared",
            }
            
            logger.info(f"Mailing pack generated: {pack_id}")
            return manifest
            
        except Exception as e:
            logger.error(f"Mailing pack generation failed: {str(e)}")
            raise MailingPackError(f"Failed to generate mailing pack: {str(e)}")

    @staticmethod
    def _generate_pdf(
        pdf_path: Path,
        prospect: Dict,
        contact: Dict,
        email_subject: str,
        email_body: str,
        before_image_path: Optional[str],
        after_image_path: Optional[str],
    ) -> None:
        c = canvas.Canvas(str(pdf_path), pagesize=A4)
        width, height = A4

        y = height - 20 * mm
        c.setFont("Helvetica-Bold", 15)
        c.drawString(20 * mm, y, "Solarware Mail Pack")
        y -= 10 * mm

        c.setFont("Helvetica-Bold", 11)
        c.drawString(20 * mm, y, "1. Prospect Info")
        y -= 6 * mm
        c.setFont("Helvetica", 10)
        lines = [
            f"Address: {prospect.get('address', '')}",
            f"Company: {prospect.get('business_name') or 'N/A'}",
            f"Industry Type: {prospect.get('business_type') or 'N/A'}",
            f"Website: {prospect.get('website') or 'N/A'}",
            f"Phone: {prospect.get('phone') or 'N/A'}",
            f"Email: {prospect.get('email') or 'N/A'}",
            f"Contact Person: {prospect.get('contact_name') or contact.get('contact_name') or 'N/A'}",
        ]
        for line in lines:
            c.drawString(22 * mm, y, line)
            y -= 5 * mm

        y -= 2 * mm
        c.setFont("Helvetica-Bold", 11)
        c.drawString(20 * mm, y, "2. Solar Opportunity")
        y -= 6 * mm
        c.setFont("Helvetica", 10)
        opportunity = [
            f"Roof size: {prospect.get('roof_area_sqm', 0):,.0f} sqm",
            f"Estimated panel count: {prospect.get('estimated_panel_count', 0)}",
            f"Estimated system size: {prospect.get('estimated_system_capacity_kw', 0):,.1f} kW",
            f"Estimated annual generation: {prospect.get('estimated_annual_production_kwh', 0):,.0f} kWh",
            f"Estimated annual savings range: R {int(prospect.get('savings_low', 0)):,} - R {int(prospect.get('savings_high', 0)):,}",
        ]
        for line in opportunity:
            c.drawString(22 * mm, y, line)
            y -= 5 * mm

        y -= 2 * mm
        c.setFont("Helvetica-Bold", 11)
        c.drawString(20 * mm, y, "3. Outreach Email")
        y -= 6 * mm
        c.setFont("Helvetica", 9)
        for line in email_body.splitlines():
            if not line.strip():
                y -= 3 * mm
            else:
                c.drawString(22 * mm, y, line[:110])
                y -= 4 * mm
            if y < 30 * mm:
                c.showPage()
                y = height - 20 * mm
                c.setFont("Helvetica", 9)

        # Render visual section on a second page when possible.
        c.showPage()
        y = height - 20 * mm
        c.setFont("Helvetica-Bold", 11)
        c.drawString(20 * mm, y, "4. Visual Concept")
        y -= 8 * mm

        try:
            if before_image_path and str(before_image_path).startswith("http"):
                import requests
                before_data = requests.get(before_image_path, timeout=15).content
                before_img = Path(pdf_path.parent) / "before_tmp.jpg"
                before_img.write_bytes(before_data)
                c.drawString(20 * mm, y, "Before image")
                c.drawImage(str(before_img), 20 * mm, y - 80 * mm, width=80 * mm, height=60 * mm, preserveAspectRatio=True)
                before_img.unlink(missing_ok=True)

            if after_image_path and Path(after_image_path).exists():
                c.drawString(110 * mm, y, "After image with panel overlay")
                c.drawImage(str(after_image_path), 110 * mm, y - 80 * mm, width=80 * mm, height=60 * mm, preserveAspectRatio=True)
        except Exception:
            c.setFont("Helvetica", 10)
            c.drawString(20 * mm, y, "Images unavailable for this pack run.")

        c.save()

    @staticmethod
    def generate_batch(
        prospects: list,
        contacts: Optional[Dict] = None,
    ) -> list:
        """Generate mailing packs for multiple prospects.
        
        Args:
            prospects: List of prospect data
            contacts: Dictionary mapping prospect_id to contact data
        
        Returns:
            List of mailing pack manifests
        """
        logger.info(f"Batch generating {len(prospects)} mailing packs")
        
        packs = []
        contacts = contacts or {}
        
        for prospect in prospects:
            try:
                contact = contacts.get(str(prospect.get("id")))
                pack = MailingPackGenerator.generate(prospect, contact)
                packs.append(pack)
            except Exception as e:
                logger.error(f"Failed to generate pack for {prospect.get('address')}: {str(e)}")
                continue
        
        logger.info(f"Batch generation complete: {len(packs)} packs generated")
        return packs
