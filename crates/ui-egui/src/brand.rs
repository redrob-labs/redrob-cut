//! The Redrob product lockup: the Redrob primary lockup, then the product name.
//!
//! The lockup files are the design system's own (`assets/brand/`, pinned by `SHA256SUMS`): the
//! white-wordmark variant on dark themes, the dark-wordmark one on light. They are drawn as they
//! are, never tinted, faded or redrawn (design system `10-logo.md`). The product name follows at
//! the UI's 600 weight in the text colour, a `space-2` gap after the lockup.

const LOCKUP_DARK_GROUND: &[u8] = include_bytes!("../../../assets/brand/redrob-logo-primary-white.png");
const LOCKUP_LIGHT_GROUND: &[u8] = include_bytes!("../../../assets/brand/redrob-logo-primary.png");

/// The product name that follows the lockup. Never inside the lockup's letterforms.
pub const PRODUCT: &str = "Cut";
/// The design system's minimum on-screen lockup height, in points.
pub const MIN_HEIGHT: f32 = 18.0;

/// The lockup for a dark (`dark = true`) or light ground. Its aspect ratio is width / height of the
/// returned texture.
pub fn lockup(ctx: &egui::Context, dark: bool) -> Option<egui::TextureHandle> {
    let id = egui::Id::new(("redrob-lockup", dark));
    if let Some(t) = ctx.data(|d| d.get_temp::<egui::TextureHandle>(id)) {
        return Some(t);
    }
    let bytes = if dark { LOCKUP_DARK_GROUND } else { LOCKUP_LIGHT_GROUND };
    let img = image::load_from_memory_with_format(bytes, image::ImageFormat::Png).ok()?;
    // Downscaled once (the files are about 3200 px wide); 1024 px stays sharp at 2x for the sizes
    // we draw. Downscaling is the only change: no tint, no crop.
    let img = img.resize(1024, 1024, image::imageops::FilterType::Lanczos3).to_rgba8();
    let color = egui::ColorImage::from_rgba_unmultiplied([img.width() as usize, img.height() as usize], img.as_raw());
    let tex = ctx.load_texture("redrob-lockup", color, egui::TextureOptions::LINEAR);
    ctx.data_mut(|d| d.insert_temp(id, tex.clone()));
    Some(tex)
}

/// Draw the product lockup `height` points tall (at least [`MIN_HEIGHT`]) with its left edge at
/// `left_center`, vertically centred. Returns the rect of lockup and name together.
pub fn paint_lockup(ui: &egui::Ui, left_center: egui::Pos2, height: f32, dark: bool, text: egui::Color32) -> Option<egui::Rect> {
    let height = height.max(MIN_HEIGHT);
    let tex = lockup(ui.ctx(), dark)?;
    let [w, h] = tex.size();
    let width = height * w as f32 / h.max(1) as f32;
    let r = egui::Rect::from_min_size(egui::pos2(left_center.x, left_center.y - height / 2.0), egui::vec2(width, height));
    ui.painter().image(tex.id(), r, egui::Rect::from_min_max(egui::pos2(0.0, 0.0), egui::pos2(1.0, 1.0)), egui::Color32::WHITE);
    // The name at the AppShell size (14 px) at least.
    let name = ui.painter().text(
        egui::pos2(r.max.x + 8.0, left_center.y),
        egui::Align2::LEFT_CENTER,
        PRODUCT,
        crate::theme::Tokens::semibold((height * 0.69).max(14.0)),
        text,
    );
    Some(r.union(name))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn both_lockups_decode_at_their_shipped_aspect() {
        let ctx = egui::Context::default();
        for dark in [true, false] {
            let t = lockup(&ctx, dark).expect("lockup decodes");
            let [w, h] = t.size();
            // the primary lockups are 5:1 (3285 x 657 and 3150 x 630)
            assert!((w as f32 / h as f32 - 5.0).abs() < 0.02, "{w}x{h}");
        }
    }
}
