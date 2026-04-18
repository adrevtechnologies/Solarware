"""Visualization generation."""
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, ImageDraw
import io
import math
import random
import requests
from ..core.logging import logger
from ..core.errors import VisualizationError
from ..utils import ensure_output_dir, save_file


class VizGenerator:
    """Generates visualizations for solar proposals."""

    @staticmethod
    async def generate_mockup(
        satellite_image_path: Optional[str],
        panel_count: int,
        roof_area_sqm: float,
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
            
            # Create geometric overlay visualization from the real satellite image.
            img = VizGenerator._create_panel_overlay(
                satellite_image_path=satellite_image_path,
                panel_count=panel_count,
                roof_area_sqm=roof_area_sqm,
                system_capacity_kw=system_capacity_kw,
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
    def _load_satellite_image(image_ref: Optional[str]) -> Image.Image:
        if not image_ref:
            raise VisualizationError("Missing satellite image")

        if image_ref.startswith("http://") or image_ref.startswith("https://"):
            response = requests.get(image_ref, timeout=20)
            response.raise_for_status()
            return Image.open(io.BytesIO(response.content)).convert("RGB")

        path = Path(image_ref)
        if not path.exists():
            raise VisualizationError(f"Satellite image path not found: {image_ref}")
        return Image.open(path).convert("RGB")

    @staticmethod
    def _panel_grid_points(
        center: Tuple[float, float],
        width: float,
        height: float,
        panel_w: float,
        panel_h: float,
        spacing: float,
    ) -> list[Tuple[float, float, float, float]]:
        cx, cy = center
        rows = max(1, int(height // (panel_h + spacing)))
        cols = max(1, int(width // (panel_w + spacing)))
        start_x = cx - (cols * (panel_w + spacing) - spacing) / 2
        start_y = cy - (rows * (panel_h + spacing) - spacing) / 2

        panels = []
        for r in range(rows):
            for c in range(cols):
                x0 = start_x + c * (panel_w + spacing)
                y0 = start_y + r * (panel_h + spacing)
                x1 = x0 + panel_w
                y1 = y0 + panel_h
                panels.append((x0, y0, x1, y1))
        return panels

    @staticmethod
    def _create_panel_overlay(
        satellite_image_path: Optional[str],
        panel_count: int,
        roof_area_sqm: float,
        system_capacity_kw: float
    ) -> Image.Image:
        """Create a geometric solar panel overlay on a real satellite image."""
        img = VizGenerator._load_satellite_image(satellite_image_path).resize((800, 600))
        draw = ImageDraw.Draw(img)

        # Approximate a roof envelope in image space and rotate panel rows.
        roof_center = (400.0, 310.0)
        roof_width = 520.0
        roof_height = 280.0
        roof_angle = -12

        panel_w = 24.0
        panel_h = 14.0
        spacing = 4.0

        base_panels = VizGenerator._panel_grid_points(
            center=roof_center,
            width=roof_width,
            height=roof_height,
            panel_w=panel_w,
            panel_h=panel_h,
            spacing=spacing,
        )

        rotation_radians = math.radians(roof_angle)
        cos_a = math.cos(rotation_radians)
        sin_a = math.sin(rotation_radians)

        cx, cy = roof_center
        placed = 0
        for x0, y0, x1, y1 in base_panels:
            if placed >= max(0, panel_count):
                break

            pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
            rotated = []
            for x, y in pts:
                rx = cx + (x - cx) * cos_a - (y - cy) * sin_a
                ry = cy + (x - cx) * sin_a + (y - cy) * cos_a
                rotated.append((rx, ry))

            draw.polygon(rotated, fill=(15, 48, 87, 220), outline=(90, 170, 255, 255))
            placed += 1

        legend = f"Panels: {placed} | Capacity: {system_capacity_kw:.1f} kW | Roof: {roof_area_sqm:.0f} sqm"
        draw.rectangle((12, 12, 620, 44), fill=(0, 0, 0, 160))
        draw.text((20, 20), legend, fill=(255, 255, 255))

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
            
            if not before_image_path or not mockup_image_path:
                raise VisualizationError("Before/after generation requires both before and after images")

            before = VizGenerator._load_satellite_image(before_image_path).resize((800, 600))
            after = VizGenerator._load_satellite_image(mockup_image_path).resize((800, 600))

            img = Image.new("RGB", (1600, 600), color="white")
            img.paste(before, (0, 0))
            img.paste(after, (800, 0))

            draw = ImageDraw.Draw(img)
            draw.rectangle((0, 0, 800, 42), fill=(0, 0, 0, 170))
            draw.rectangle((800, 0, 1600, 42), fill=(0, 0, 0, 170))
            draw.text((16, 12), "Before", fill=(255, 255, 255))
            draw.text((816, 12), "After (Panel Overlay)", fill=(255, 255, 255))
            
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

