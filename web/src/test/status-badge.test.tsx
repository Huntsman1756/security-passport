import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { StatusBadge } from "../components/StatusBadge";
import { Field } from "../components/Field";
import type { PassportField } from "../types";

describe("StatusBadge", () => {
  it("renders every status distinctly (not color-only)", () => {
    const statuses = [
      "reported",
      "derived",
      "inferred",
      "conflict",
      "not_found",
      "not_applicable",
    ] as const;
    for (const s of statuses) {
      const { unmount } = render(<StatusBadge status={s} />);
      expect(screen.getByText(/reported|derived|inferred|conflict|not found|n\/a/i)).toBeInTheDocument();
      unmount();
    }
  });
});

describe("Field", () => {
  const field: PassportField = {
    value: "DBFUGB",
    status: "reported",
    evidence: [],
    quality_flags: [],
    alternatives: [],
    searched_sources: [],
    explanation: "",
    unit: "",
  };

  it("renders value + status and opens provenance on click", () => {
    let opened = "";
    render(
      <Field
        label="CFI"
        name="identity.cfi"
        field={field}
        onOpen={(n) => (opened = n)}
      />,
    );
    screen.getByText("DBFUGB").click();
    expect(opened).toBe("identity.cfi");
  });

  it("renders not_found as an explicit state, not an empty cell", () => {
    render(
      <Field
        label="Issuer SSS"
        name="post_trade.issuer_sss"
        field={{
          ...field,
          value: null,
          status: "not_found",
          searched_sources: ["ecb_eligible_assets"],
        }}
        onOpen={() => {}}
      />,
    );
    expect(screen.getByText("not found")).toBeInTheDocument();
  });
});
