"""Visualization generation."""
from pathlib import Path
from typing import Optional, Tuple, List
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
        roof_polygon: Optional[List[Tuple[float, float]]] = None,
        image_bbox: Optional[Tuple[float, float, float, float]] = None,
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
                roof_polygon=roof_polygon,
                image_bbox=image_bbox,
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
    def _point_in_polygon(point: Tuple[float, float], polygon: List[Tuple[float, float]]) -> bool:
        x, y = point
        inside = False
        j = len(polygon) - 1
        for i in range(len(polygon)):
            xi, yi = polygon[i]
            xj, yj = polygon[j]
            intersects = ((yi > y) != (yj > y)) and (
                x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi
            )
            if intersects:
                inside = not inside
            j = i
        return inside

    @staticmethod
    def _geo_polygon_to_pixel(
        polygon: List[Tuple[float, float]],
        image_bbox: Tuple[float, float, float, float],
        width: int,
        height: int,
    ) -> List[Tuple[float, float]]:
        min_lat, max_lat, min_lon, max_lon = image_bbox
        lat_span = (max_lat - min_lat) or 1e-9
        lon_span = (max_lon - min_lon) or 1e-9

        px = []
        for lat, lon in polygon:
            x = (lon - min_lon) / lon_span * width
            y = (max_lat - lat) / lat_span * height
            px.append((x, y))
        return px

    @staticmethod
    def _polygon_area_px(polygon: List[Tuple[float, float]]) -> float:
        if len(polygon) < 3:
            return 0.0
        area = 0.0
        for i in range(len(polygon)):
            x1, y1 = polygon[i]
            x2, y2 = polygon[(i + 1) % len(polygon)]
            area += (x1 * y2) - (x2 * y1)
        return abs(area) / 2.0

    @staticmethod
    def _draw_panels_in_polygon(
        draw: ImageDraw.ImageDraw,
        polygon_px: List[Tuple[float, float]],
        panel_count: int,
        roof_area_sqm: float,
    ) -> int:
        xs = [p[0] for p in polygon_px]
        ys = [p[1] for p in polygon_px]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        panel_footprint_sqm = 2.2
        panel_aspect = 1.8  # Typical portrait panel ratio (length / width)
        polygon_area_px = VizGenerator._polygon_area_px(polygon_px)

        if roof_area_sqm > 0 and polygon_area_px > 0:
            panel_px_area = (panel_footprint_sqm / roof_area_sqm) * polygon_area_px
            panel_h = max(2.0, math.sqrt(panel_px_area / panel_aspect))
            panel_w = max(4.0, panel_h * panel_aspect)
            spacing = max(1.0, min(panel_w, panel_h) * 0.12)
        else:
            panel_w = 22.0
            panel_h = 12.0
            spacing = 3.0

        placed = 0
        y = min_y
        while y + panel_h <= max_y and placed < panel_count:
            x = min_x
            while x + panel_w <= max_x and placed < panel_count:
                corners = [
                    (x, y),
                    (x + panel_w, y),
                    (x + panel_w, y + panel_h),
                    (x, y + panel_h),
                ]
                if all(VizGenerator._point_in_polygon(c, polygon_px) for c in corners):
                    draw.polygon(corners, fill=(15, 48, 87, 220), outline=(90, 170, 255, 255))
                    placed += 1
                x += panel_w + spacing
            y += panel_h + spacing

        return placed

    @staticmethod
    def _create_panel_overlay(
        satellite_image_path: Optional[str],
        panel_count: int,
        roof_area_sqm: float,
        system_capacity_kw: float,
        roof_polygon: Optional[List[Tuple[float, float]]] = None,
        image_bbox: Optional[Tuple[float, float, float, float]] = None,
    ) -> Image.Image:
        """Create a geometric solar panel overlay on a real satellite image."""
        img = VizGenerator._load_satellite_image(satellite_image_path)
        width, height = img.size
        draw = ImageDraw.Draw(img)

        placed = 0

        if roof_polygon and image_bbox and len(roof_polygon) >= 3:
            polygon_px = VizGenerator._geo_polygon_to_pixel(
                polygon=roof_polygon,
                image_bbox=image_bbox,
                width=width,
                height=height,
            )
            draw.polygon(polygon_px, outline=(255, 64, 64, 255), width=3)
            placed = VizGenerator._draw_panels_in_polygon(
                draw=draw,
                polygon_px=polygon_px,
                panel_count=max(0, panel_count),
                roof_area_sqm=max(0.0, roof_area_sqm),
            )

        if placed > 0:
            legend = f"Panels: {placed} | Capacity: {system_capacity_kw:.1f} kW | Roof: {roof_area_sqm:.0f} sqm"
            draw.rectangle((12, 12, 620, 44), fill=(0, 0, 0, 160))
            draw.text((20, 20), legend, fill=(255, 255, 255))
            return img

        # Approximate a roof envelope in image space and rotate panel rows.
        roof_center = (width / 2.0, height / 2.0)
        roof_width = width * 0.65
        roof_height = height * 0.46
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

