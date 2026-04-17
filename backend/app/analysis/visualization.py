"""Visualization generation."""
from typing import Dict, Optional
from PIL import Image, ImageDraw, ImageFont
import io
import random
from app.core.logging import logger
from app.core.errors import VisualizationError
from app.utils import ensure_output_dir, save_file


class VizGenerator:
    """Generates visualizations for solar proposals."""

    @staticmethod
    async def generate_mockup(
        satellite_image_path: Optional[str],
        panel_count: int,
        roof_area_sqft: float,
        system_capacity_kw: float,
        output_path: Optional[str] = None,
    ) -> str:
        """Generate solar panel mockup visualization.
        
        Args:
            satellite_image_path: Path to satellite image
            panel_count: Number of panels
            roof_area_sqft: Roof area in square feet
            system_capacity_kw: System capacity in kW
            output_path: Optional specific output path
        
        Returns:
            Path to generated mockup image
        
        Raises:
            VisualizationError: If generation fails
        """
        try:
            logger.info(f"Generating mockup for {panel_count} panels")
            
            # Create mock visualization
            img = VizGenerator._create_mock_mockup(
                panel_count,
                roof_area_sqft,
                system_capacity_kw
            )
            
            # Save image
            output_dir = ensure_output_dir("visualizations")
            filename = f"mockup_{random.randint(1000, 9999)}.png"
            
            img_bytes = io.BytesIO()
            img.save(img_bytes, format="PNG")
            img_bytes.seek(0)
            
            saved_path = save_file(img_bytes.read(), output_dir, filename)
            logger.info(f"Mockup saved to {saved_path}")
            
            return str(saved_path)
            
        except Exception as e:
            logger.error(f"Mockup generation failed: {str(e)}")
            raise VisualizationError(f"Failed to generate mockup: {str(e)}")

    @staticmethod
    def _create_mock_mockup(
        panel_count: int,
        roof_area_sqft: float,
        system_capacity_kw: float
    ) -> Image.Image:
        """Create a mock mockup image."""
        # Create image with blue gradient background (simulating satellite)
        img = Image.new("RGB", (800, 600), color=(100, 150, 200))
        draw = ImageDraw.Draw(img)
        
        # Draw some building outline
        draw.rectangle([100, 200, 700, 450], outline="white", width=3)
        
        # Draw grid of solar panels
        panel_width = 40
        panel_height = 35
        start_x = 150
        start_y = 250
        
        panels_per_row = max(1, int((700 - 150) / (panel_width + 5)))
        rows = max(1, int(panel_count / panels_per_row) + 1)
        
        for i in range(min(panel_count, panels_per_row * rows)):
            row = i // panels_per_row
            col = i % panels_per_row
            x = start_x + col * (panel_width + 5)
            y = start_y + row * (panel_height + 5)
            
            if x + panel_width < 700 and y + panel_height < 500:
                draw.rectangle(
                    [x, y, x + panel_width, y + panel_height],
                    fill=(50, 100, 150),
                    outline=(100, 200, 255),
                    width=1
                )
        
        # Add text
        try:
            font = ImageFont.load_default()
        except:
            font = None
        
        text_lines = [
            f"Solar Proposal",
            f"Panels: {panel_count} | Capacity: {system_capacity_kw:.1f} kW",
            f"Roof Area: {roof_area_sqft:,.0f} sq ft",
        ]
        
        for i, text in enumerate(text_lines):
            y_pos = 50 + i * 30
            draw.text((20, y_pos), text, fill="white", font=font)
        
        return img

    @staticmethod
    async def generate_before_after(
        before_image_path: Optional[str],
        mockup_image_path: Optional[str],
        output_path: Optional[str] = None,
    ) -> str:
        """Generate before/after comparison image.
        
        Args:
            before_image_path: Path to before (satellite) image
            mockup_image_path: Path to mockup image
            output_path: Optional specific output path
        
        Returns:
            Path to generated comparison image
        """
        try:
            logger.info("Generating before/after comparison")
            
            # Create side-by-side comparison
            img = VizGenerator._create_before_after_image()
            
            # Save
            output_dir = ensure_output_dir("visualizations")
            filename = f"before_after_{random.randint(1000, 9999)}.png"
            
            img_bytes = io.BytesIO()
            img.save(img_bytes, format="PNG")
            img_bytes.seek(0)
            
            saved_path = save_file(img_bytes.read(), output_dir, filename)
            logger.info(f"Comparison saved to {saved_path}")
            
            return str(saved_path)
            
        except Exception as e:
            logger.error(f"Before/after generation failed: {str(e)}")
            raise VisualizationError(f"Failed to generate comparison: {str(e)}")

    @staticmethod
    def _create_before_after_image() -> Image.Image:
        """Create before/after comparison image."""
        # Create wide image with two sections
        img = Image.new("RGB", (1600, 600), color="white")
        draw = ImageDraw.Draw(img)
        
        # Left side - before
        draw.rectangle([0, 0, 800, 600], fill=(100, 150, 200))
        try:
            font = ImageFont.load_default()
        except:
            font = None
        draw.text((600, 300), "BEFORE", fill="white", font=font)
        
        # Right side - after
        draw.rectangle([800, 0, 1600, 600], fill=(100, 200, 100))
        draw.text((1350, 300), "AFTER", fill="white", font=font)
        
        return img
