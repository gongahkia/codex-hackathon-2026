"""Generate a minimal Remotion project bundle for runtime renders."""

from __future__ import annotations

from pathlib import Path


INDEX_JSX = """import {registerRoot} from 'remotion';
import {RemotionRoot} from './Root';

registerRoot(RemotionRoot);
"""


ROOT_JSX = """import React from 'react';
import {Composition} from 'remotion';
import {MainVideo} from './MainVideo';

export const RemotionRoot = () => {
  return (
    <Composition
      id="Main"
      component={MainVideo}
      durationInFrames={5400}
      fps={30}
      width={1280}
      height={720}
      defaultProps={{fps: 30, scenes: []}}
    />
  );
};
"""


MAIN_VIDEO_JSX = """import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';

const resolveScene = (scenes, fps, frame) => {
  let cursor = 0;
  for (const scene of scenes) {
    const durationFrames = Math.max(1, Math.floor((scene.duration_sec || 1) * fps));
    const upper = cursor + durationFrames;
    if (frame >= cursor && frame < upper) {
      return scene;
    }
    cursor = upper;
  }
  return scenes[scenes.length - 1] || {title: 'Demo', narration: 'No scenes generated.'};
};

export const MainVideo = ({scenes = [], fps = 30}) => {
  const frame = useCurrentFrame();
  const currentScene = resolveScene(scenes, fps, frame);
  const style = currentScene.style || 'pitch';

  return (
    <AbsoluteFill
      style={{
        background: style === 'walkthrough' ? '#0B172A' : '#1D2D50',
        color: '#F3F6F9',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        padding: 80,
        fontFamily: 'ui-sans-serif, system-ui, -apple-system',
      }}
    >
      <h1 style={{fontSize: 68, marginBottom: 24, textAlign: 'center'}}>{currentScene.title || 'Scene'}</h1>
      <p style={{fontSize: 34, maxWidth: 1000, lineHeight: 1.35, textAlign: 'center'}}>
        {currentScene.narration || 'Narration placeholder'}
      </p>
      <p style={{opacity: 0.7, marginTop: 36, fontSize: 20}}>Frame {frame}</p>
    </AbsoluteFill>
  );
};
"""


def ensure_remotion_bundle(workspace: str | Path) -> Path:
    """Write a deterministic Remotion bundle and return its entry path."""

    root = Path(workspace) / "remotion"
    root.mkdir(parents=True, exist_ok=True)

    (root / "index.jsx").write_text(INDEX_JSX, encoding="utf-8")
    (root / "Root.jsx").write_text(ROOT_JSX, encoding="utf-8")
    (root / "MainVideo.jsx").write_text(MAIN_VIDEO_JSX, encoding="utf-8")

    return root / "index.jsx"
