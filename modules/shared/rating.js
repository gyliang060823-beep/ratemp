export function ratingStars(score) {
  const value = Number(score || 0);
  const rounded = Math.round(value);
  const label = value ? `${value.toFixed(1)} / 5` : "暂无评分";
  const stars = Array.from({ length: 5 }, (_, index) => {
    const filled = index < rounded;
    return `<span class="star ${filled ? "filled" : ""}" aria-hidden="true">★</span>`;
  }).join("");

  return `
    <span class="rating-stars" aria-label="${label}">
      <span class="stars">${stars}</span>
      <span class="rating-label">${label}</span>
    </span>
  `;
}
