/**
 * Style definitions for ML behavior types.
 * Keys match the frozen KMeans output: "Persistent" | "Transient"
 *
 * NOTE: These are NOT renamed to Normal/Abnormal — that mapping
 * is explicitly forbidden by the ML integration contract.
 */
export const behaviorStyle = {
  "Persistent": {
    color: "#0F6B6E",
    label: "Persistent",
    description: "KMeans Cluster 1 — sustained thermal presence over multiple days",
  },
  "Transient": {
    color: "#D9A521",
    label: "Transient",
    description: "KMeans Cluster 0 — short-duration or irregular thermal activity",
  },
};
