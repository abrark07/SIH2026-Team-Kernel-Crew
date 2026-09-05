/**
 * Style definitions for ML classification values.
 * Keys match the ML final_prediction field: "Industrial" | "Uncertain"
 */
export const classStyle = {
  "Industrial": {
    color: "#0F6B6E",
    label: "Industrial Source",
    description: "Persistent thermal signature consistent with industrial activity",
  },
  "Uncertain": {
    color: "#D9A521",
    label: "Uncertain",
    description: "Thermal signature does not confidently match industrial patterns",
  },
};
