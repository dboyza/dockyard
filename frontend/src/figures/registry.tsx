import type { ReactElement } from "react";
import type { FigureId } from "../contracts.gen";
import { QuorumModel } from "../QuorumModel";
import { ReconciliationModel } from "../ReconciliationModel";
import { StorageModel } from "../StorageModel";
import { dispatch } from "./dispatch";
import { docker } from "./docker";
import { foundations } from "./foundations";
import { kubernetes } from "./kubernetes";

export type Drawing = (props: { step?: number }) => ReactElement;
export type Drawings = Partial<Record<FigureId, Drawing>>;

const models = {
  "reconciliation-model": () => <ReconciliationModel />,
  "storage-model": () => <StorageModel />,
  "quorum-model": () => <QuorumModel />,
} satisfies Drawings;

// Typed as a complete record: a figure added to figures.json without a drawing
// here fails the TypeScript check after the contracts are regenerated.
export const drawings: Record<FigureId, Drawing> = {
  ...foundations,
  ...dispatch,
  ...docker,
  ...kubernetes,
  ...models,
};

export function isFigureId(id: string): id is FigureId {
  return Object.hasOwn(drawings, id);
}
