"""Mailing pack generation services."""
from typing import Dict, Optional
from datetime import datetime
from jinja2 import Template
import uuid
from ..core.logging import logger
from ..core.errors import MailingPackError
from ..utils import ensure_output_dir, save_file


class MailingPackGenerator:
    """Generates mailing packs for prospects."""

    # Email template
    PROSPECT_EMAIL_TEMPLATE = """Subject: {{subject}}

Dear {{recipient_name}},

We've reviewed your property at {{address}} and identified strong rooftop solar suitability for commercial outreach.

PROPERTY ANALYSIS SUMMARY:
- Building Address: {{address}}
- Roof Area: {{roof_area_sqft:,}} sq ft ({{roof_area_sqm:,.0f}} sq m)
- Estimated System Size: {{system_capacity_kw}} kW
- Roof Suitability Score: {{suitability_score}}/100
- Opportunity Tier: {{opportunity_tier}}

SOLAR INSTALLATION PROPOSAL:
- Recommended Panel Count: {{panel_count}} solar panels
- System Configuration: {{system_capacity_kw}} kW capacity
- Expected Payback Period: {{payback_years}} years (typical)
- System Efficiency: {{system_efficiency:.0%}}

OPPORTUNITY SNAPSHOT:
- Suitable roof area and clear panel layout potential
- Commercial-scale rooftop suitable for a discovery call
- Visual proposal generated for quick decision support

NEXT STEPS:
We've prepared detailed visual mockups of how solar panels would look on your roof,
included in this proposal. We'd love to discuss how solar can benefit your business.

Please feel free to contact us at your convenience to schedule a consultation.

Best regards,
Solar Energy Team
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
        roof_area_sqft = int(prospect.get("roof_area_sqft") or 0)
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
            recipient_name = contact.get("contact_name", "Valued Prospect")
            
            suitability_score = int(round((prospect.get("solar_confidence") or 0.0) * 100))
            opportunity_tier = MailingPackGenerator._opportunity_tier(suitability_score)
            
            email_subject = f"Solar Installation Proposal: {prospect.get('business_name', 'Your Property')}"

            # Render email
            template = Template(MailingPackGenerator.PROSPECT_EMAIL_TEMPLATE)
            email_body = template.render(
                subject=email_subject,
                recipient_name=recipient_name,
                address=prospect.get("address", "Unknown Address"),
                roof_area_sqft=prospect.get("roof_area_sqft", 0),
                roof_area_sqm=prospect.get("roof_area_sqm", 0),
                system_capacity_kw=prospect.get("estimated_system_capacity_kw", 0),
                annual_production_kwh=prospect.get("estimated_annual_production_kwh") or 0,
                panel_count=prospect.get("estimated_panel_count", 0),
                suitability_score=suitability_score,
                opportunity_tier=opportunity_tier,
                system_efficiency=0.82,
            )
            
            # Create mailing pack directory
            pack_id = str(uuid.uuid4())
            pack_dir = ensure_output_dir(f"mailing_packs/{pack_id}")
            
            # Save email content
            email_filename = f"email_{pack_id}.txt"
            email_path = pack_dir / email_filename
            with open(email_path, "w") as f:
                f.write(email_body)
            
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
                "email_path": str(email_path),
                "satellite_image_path": satellite_image_path,
                "mockup_image_path": mockup_image_path,
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
