"use client";

import { createContext, useContext } from "react";

export type PlaybackMode = "autoplay" | "manual-auto-audio" | "manual";

export interface PresentationContextType {
  playbackMode: PlaybackMode;
  nextSlide: () => void;
  muted: boolean;
}

const defaultContext: PresentationContextType = {
  playbackMode: "manual",
  nextSlide: () => {},
  muted: false,
};

export const PresentationContext = createContext<PresentationContextType>(defaultContext);

export function usePresentation() {
  return useContext(PresentationContext);
}
