"""Visualization generation."""
from pathlib import Path
from typing import Optional, Tuple, List
from PIL import Image, ImageDraw, ImageStat
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
        source_image: Image.Image,
        polygon_px: List[Tuple[float, float]],
        panel_count: int,
        roof_area_sqm: float,
    ) -> int:
        panel_long_m = 1.72
        panel_short_m = 1.13
        panel_footprint_sqm = panel_long_m * panel_short_m
        gap_m = 0.02
        setback_m = 0.5
        service_gap_m = 0.6

        def rotate_point(x: float, y: float, angle: float) -> Tuple[float, float]:
            c = math.cos(angle)
            s = math.sin(angle)
            return (x * c - y * s, x * s + y * c)

        def min_distance_to_edges(point: Tuple[float, float], poly: List[Tuple[float, float]]) -> float:
            px, py = point
            min_d = float("inf")
            for i in range(len(poly)):
                x1, y1 = poly[i]
                x2, y2 = poly[(i + 1) % len(poly)]
                vx, vy = x2 - x1, y2 - y1
                wx, wy = px - x1, py - y1
                edge_len_sq = vx * vx + vy * vy
                if edge_len_sq <= 1e-9:
                    d = math.hypot(px - x1, py - y1)
                else:
                    t = max(0.0, min(1.0, (wx * vx + wy * vy) / edge_len_sq))
                    proj_x, proj_y = x1 + t * vx, y1 + t * vy
                    d = math.hypot(px - proj_x, py - proj_y)
                if d < min_d:
                    min_d = d
            return min_d

        def obstruction_score(img: Image.Image, corners: List[Tuple[float, float]]) -> float:
            xs = [p[0] for p in corners]
            ys = [p[1] for p in corners]
            min_x = max(0, int(min(xs)))
            min_y = max(0, int(min(ys)))
            max_x = min(img.width, int(max(xs)) + 1)
            max_y = min(img.height, int(max(ys)) + 1)
            if max_x - min_x < 3 or max_y - min_y < 3:
                return 0.0
            patch = img.crop((min_x, min_y, max_x, max_y)).convert("L")
            stats = ImageStat.Stat(patch)
            std = stats.stddev[0] if stats.stddev else 0.0
            mean = stats.mean[0] if stats.mean else 0.0
            if mean > 215 and std > 18:
                return 1.0
            return min(1.0, std / 65.0)

        def draw_panel_style(corners: List[Tuple[float, float]]) -> None:
            cx = sum(p[0] for p in corners) / 4.0
            cy = sum(p[1] for p in corners) / 4.0
            shadow = [(p[0] + 1.4, p[1] + 1.8) for p in corners]
            draw.polygon(shadow, fill=(0, 0, 0, 70))

            draw.polygon(corners, fill=(12, 30, 54, 235), outline=(168, 175, 186, 220))

            for t in (0.25, 0.5, 0.75):
                x1 = corners[0][0] + (corners[1][0] - corners[0][0]) * t
                y1 = corners[0][1] + (corners[1][1] - corners[0][1]) * t
                x2 = corners[3][0] + (corners[2][0] - corners[3][0]) * t
                y2 = corners[3][1] + (corners[2][1] - corners[3][1]) * t
                draw.line((x1, y1, x2, y2), fill=(195, 203, 214, 115), width=1)

            draw.line((corners[0], corners[2]), fill=(255, 255, 255, 26), width=1)

        if len(polygon_px) < 3 or roof_area_sqm <= 0:
            return 0

        # Determine dominant roof axis for grid alignment.
        cx = sum(x for x, _ in polygon_px) / len(polygon_px)
        cy = sum(y for _, y in polygon_px) / len(polygon_px)
        xx = sum((x - cx) ** 2 for x, _ in polygon_px)
        yy = sum((y - cy) ** 2 for _, y in polygon_px)
        xy = sum((x - cx) * (y - cy) for x, y in polygon_px)
        theta = 0.5 * math.atan2(2 * xy, xx - yy)

        local_poly = []
        for x, y in polygon_px:
            lx, ly = rotate_point(x - cx, y - cy, -theta)
            local_poly.append((lx, ly))

        min_u = min(p[0] for p in local_poly)
        max_u = max(p[0] for p in local_poly)
        min_v = min(p[1] for p in local_poly)
        max_v = max(p[1] for p in local_poly)

        polygon_area_px = VizGenerator._polygon_area_px(polygon_px)
        if polygon_area_px <= 0:
            return 0

        meters_per_px = math.sqrt(roof_area_sqm / polygon_area_px)
        if meters_per_px <= 0:
            return 0

        roof_width_m = (max_u - min_u) * meters_per_px
        roof_height_m = (max_v - min_v) * meters_per_px

        if roof_width_m >= roof_height_m:
            panel_w_m, panel_h_m = panel_long_m, panel_short_m
        else:
            panel_w_m, panel_h_m = panel_short_m, panel_long_m

        panel_w_px = panel_w_m / meters_per_px
        panel_h_px = panel_h_m / meters_per_px
        gap_px = max(1.0, gap_m / meters_per_px)
        setback_px = max(2.0, setback_m / meters_per_px)
        service_gap_px = max(2.0, service_gap_m / meters_per_px)

        # Perspective hint: compress panels slightly toward one roof side based on axis angle.
        perspective_strength = 0.08 if abs(math.sin(theta)) > 0.35 else 0.04

        placed = 0
        row_index = 0
        v = min_v + setback_px
        usable_v = max(1.0, (max_v - min_v) - (2 * setback_px))

        while v + panel_h_px <= max_v - setback_px and placed < panel_count:
            if row_index > 0 and row_index % 2 == 0:
                v += service_gap_px

            col_index = 0
            u = min_u + setback_px
            while u + panel_w_px <= max_u - setback_px and placed < panel_count:
                if col_index > 0 and col_index % 8 == 0:
                    u += service_gap_px

                row_progress = max(0.0, min(1.0, (v - (min_v + setback_px)) / usable_v))
                width_scale = 1.0 - (perspective_strength * (1.0 - row_progress))

                panel_cx = u + panel_w_px / 2.0
                panel_cy = v + panel_h_px / 2.0
                half_w = (panel_w_px / 2.0) * width_scale
                half_h = panel_h_px / 2.0
                local_corners = [
                    (panel_cx - half_w, panel_cy - half_h),
                    (panel_cx + half_w, panel_cy - half_h),
                    (panel_cx + half_w, panel_cy + half_h),
                    (panel_cx - half_w, panel_cy + half_h),
                ]

                corners = []
                for lu, lv in local_corners:
                    gx, gy = rotate_point(lu, lv, theta)
                    corners.append((gx + cx, gy + cy))

                is_inside = all(VizGenerator._point_in_polygon(p, polygon_px) for p in corners)
                has_setback = all(min_distance_to_edges(p, polygon_px) >= setback_px for p in corners)

                if is_inside and has_setback:
                    obstruction = obstruction_score(source_image, corners)
                    if obstruction < 0.45:
                        draw_panel_style(corners)
                        placed += 1

                u += panel_w_px + gap_px
                col_index += 1

            v += panel_h_px + gap_px
            row_index += 1

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
        base_img = VizGenerator._load_satellite_image(satellite_image_path)
        width, height = base_img.size
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay, "RGBA")

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
                source_image=base_img,
                polygon_px=polygon_px,
                panel_count=max(0, panel_count),
                roof_area_sqm=max(0.0, roof_area_sqm),
            )

        if placed >= 6:
            out = Image.alpha_composite(base_img.convert("RGBA"), overlay).convert("RGB")
            out_draw = ImageDraw.Draw(out)
            legend = f"Panels: {placed} | Capacity: {system_capacity_kw:.1f} kW | Roof: {roof_area_sqm:.0f} sqm"
            out_draw.rectangle((12, 12, 620, 44), fill=(0, 0, 0, 160))
            out_draw.text((20, 20), legend, fill=(255, 255, 255))
            return out

        if placed > 0:
            # Quality rule: skip mockup when very few panels fit.
            out = base_img.copy()
            out_draw = ImageDraw.Draw(out)
            note = "Install mockup skipped: fewer than 6 panels fit roof constraints"
            out_draw.rectangle((12, 12, 760, 44), fill=(0, 0, 0, 160))
            out_draw.text((20, 20), note, fill=(255, 255, 255))
            return out

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

        if placed < 6:
            out = base_img.copy()
            out_draw = ImageDraw.Draw(out)
            note = "Install mockup skipped: fewer than 6 panels fit roof constraints"
            out_draw.rectangle((12, 12, 760, 44), fill=(0, 0, 0, 160))
            out_draw.text((20, 20), note, fill=(255, 255, 255))
            return out

        out = Image.alpha_composite(base_img.convert("RGBA"), overlay).convert("RGB")
        out_draw = ImageDraw.Draw(out)
        legend = f"Panels: {placed} | Capacity: {system_capacity_kw:.1f} kW | Roof: {roof_area_sqm:.0f} sqm"
        out_draw.rectangle((12, 12, 620, 44), fill=(0, 0, 0, 160))
        out_draw.text((20, 20), legend, fill=(255, 255, 255))

        return out

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

