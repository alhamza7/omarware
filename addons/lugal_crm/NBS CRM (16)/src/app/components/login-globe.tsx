import { useEffect, useRef } from "react";
import * as THREE from "three";

interface LoginGlobeProps {
  isDark?: boolean;
}

/* ── Convert lat/lng (degrees) → 3D position on sphere ── */
function latLngToVector3(lat: number, lng: number, radius: number): THREE.Vector3 {
  const phi = (90 - lat) * (Math.PI / 180);
  const theta = (lng + 180) * (Math.PI / 180);
  return new THREE.Vector3(
    -(radius * Math.sin(phi) * Math.cos(theta)),
    radius * Math.cos(phi),
    radius * Math.sin(phi) * Math.sin(theta),
  );
}

/* ── Atmosphere Shader (Fresnel-based glow) ── */
const atmosphereVertexShader = `
  varying vec3 vNormal;
  varying vec3 vPosition;
  void main() {
    vNormal = normalize(normalMatrix * normal);
    vPosition = (modelViewMatrix * vec4(position, 1.0)).xyz;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const atmosphereFragmentShader = `
  uniform vec3 uColor;
  uniform float uIntensity;
  varying vec3 vNormal;
  varying vec3 vPosition;
  void main() {
    vec3 viewDir = normalize(-vPosition);
    float fresnel = 1.0 - dot(viewDir, vNormal);
    fresnel = pow(fresnel, 3.0) * uIntensity;
    gl_FragColor = vec4(uColor, fresnel * 0.85);
  }
`;

/* ── Marker pulse ring shader ── */
const ringVertexShader = `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const ringFragmentShader = `
  uniform vec3 uColor;
  uniform float uTime;
  varying vec2 vUv;
  void main() {
    float dist = length(vUv - vec2(0.5));
    float ring = smoothstep(0.35, 0.4, dist) * (1.0 - smoothstep(0.45, 0.5, dist));
    float pulse = 0.5 + 0.5 * sin(uTime * 3.0);
    float alpha = ring * pulse;
    gl_FragColor = vec4(uColor, alpha);
  }
`;

export function LoginGlobe({ isDark = true }: LoginGlobeProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const frameRef = useRef<number>(0);
  const isDarkRef = useRef(isDark);
  isDarkRef.current = isDark;

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    /* ── Scene setup ── */
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 1000);
    camera.position.z = 2.8;

    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: "high-performance",
    });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000000, 0);
    container.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    /* ── Lighting ── */
    const ambientLight = new THREE.AmbientLight(0xffffff, isDark ? 0.15 : 0.4);
    scene.add(ambientLight);

    const sunLight = new THREE.DirectionalLight(0xffffff, isDark ? 1.8 : 1.4);
    sunLight.position.set(5, 3, 5);
    scene.add(sunLight);

    // Subtle fill light from opposite side
    const fillLight = new THREE.DirectionalLight(
      isDark ? 0x334488 : 0x88ccdd,
      isDark ? 0.3 : 0.2,
    );
    fillLight.position.set(-5, -1, -3);
    scene.add(fillLight);

    /* ── Texture loader ── */
    const loader = new THREE.TextureLoader();
    loader.crossOrigin = "anonymous";

    /* ── Earth sphere ── */
    const earthGeometry = new THREE.SphereGeometry(1, 64, 64);
    const earthMaterial = new THREE.MeshPhongMaterial({
      color: 0xffffff,
      shininess: 25,
      specular: new THREE.Color(isDark ? 0x333333 : 0x444444),
    });

    const earth = new THREE.Mesh(earthGeometry, earthMaterial);
    scene.add(earth);

    // Load Earth texture
    loader.load(
      "https://unpkg.com/three-globe@2.31.1/example/img/earth-blue-marble.jpg",
      (texture) => {
        texture.colorSpace = THREE.SRGBColorSpace;
        earthMaterial.map = texture;
        earthMaterial.needsUpdate = true;
      },
    );

    // Load bump map for terrain relief
    loader.load(
      "https://unpkg.com/three-globe@2.31.1/example/img/earth-topology.png",
      (texture) => {
        earthMaterial.bumpMap = texture;
        earthMaterial.bumpScale = 0.015;
        earthMaterial.needsUpdate = true;
      },
    );

    /* ── Cloud layer ── */
    const cloudGeometry = new THREE.SphereGeometry(1.008, 64, 64);
    const cloudMaterial = new THREE.MeshPhongMaterial({
      transparent: true,
      opacity: 0.25,
      depthWrite: false,
    });
    const clouds = new THREE.Mesh(cloudGeometry, cloudMaterial);
    scene.add(clouds);

    loader.load(
      "https://unpkg.com/three-globe@2.31.1/example/img/earth-water.png",
      (texture) => {
        cloudMaterial.alphaMap = texture;
        cloudMaterial.needsUpdate = true;
      },
    );

    /* ── Atmosphere glow ── */
    const atmosColor = isDark
      ? new THREE.Color(0.3, 0.5, 1.0)
      : new THREE.Color(0.0, 0.7, 0.85);
    const atmosphereGeometry = new THREE.SphereGeometry(1.18, 64, 64);
    const atmosphereMaterial = new THREE.ShaderMaterial({
      vertexShader: atmosphereVertexShader,
      fragmentShader: atmosphereFragmentShader,
      uniforms: {
        uColor: { value: atmosColor },
        uIntensity: { value: isDark ? 1.5 : 1.2 },
      },
      side: THREE.BackSide,
      transparent: true,
      depthWrite: false,
    });
    const atmosphere = new THREE.Mesh(atmosphereGeometry, atmosphereMaterial);
    scene.add(atmosphere);

    /* ── Iraq Marker Group (attached to earth so it rotates with it) ── */
    const markerGroup = new THREE.Group();
    earth.add(markerGroup);

    // Baghdad coordinates: 33.3152°N, 44.3661°E
    const baghdadPos = latLngToVector3(33.3152, 44.3661, 1.0);

    // Golden sphere marker
    const markerColor = isDark ? 0xd4af37 : 0x06b6d4;
    const markerGeometry = new THREE.SphereGeometry(0.022, 16, 16);
    const markerMaterial = new THREE.MeshBasicMaterial({
      color: markerColor,
    });
    const marker = new THREE.Mesh(markerGeometry, markerMaterial);
    marker.position.copy(baghdadPos);
    markerGroup.add(marker);

    // Outer glow sphere
    const glowGeometry = new THREE.SphereGeometry(0.04, 16, 16);
    const glowMaterial = new THREE.MeshBasicMaterial({
      color: markerColor,
      transparent: true,
      opacity: 0.3,
      depthWrite: false,
    });
    const glowSphere = new THREE.Mesh(glowGeometry, glowMaterial);
    glowSphere.position.copy(baghdadPos);
    markerGroup.add(glowSphere);

    // Pulse ring (flat disc on Earth surface pointing outward)
    const ringGeometry = new THREE.PlaneGeometry(0.12, 0.12);
    const ringMaterial = new THREE.ShaderMaterial({
      vertexShader: ringVertexShader,
      fragmentShader: ringFragmentShader,
      uniforms: {
        uColor: { value: new THREE.Color(markerColor) },
        uTime: { value: 0 },
      },
      transparent: true,
      depthWrite: false,
      side: THREE.DoubleSide,
    });
    const ring = new THREE.Mesh(ringGeometry, ringMaterial);
    ring.position.copy(baghdadPos);
    // Orient ring to face outward from the sphere center
    ring.lookAt(baghdadPos.clone().multiplyScalar(2));
    markerGroup.add(ring);

    // Vertical beam (thin cylinder pointing outward)
    const beamGeometry = new THREE.CylinderGeometry(0.003, 0.003, 0.12, 8);
    const beamMaterial = new THREE.MeshBasicMaterial({
      color: markerColor,
      transparent: true,
      opacity: 0.5,
      depthWrite: false,
    });
    const beam = new THREE.Mesh(beamGeometry, beamMaterial);
    // Position beam starting from surface going outward
    const beamDir = baghdadPos.clone().normalize();
    const beamCenter = baghdadPos.clone().add(beamDir.clone().multiplyScalar(0.06));
    beam.position.copy(beamCenter);
    // Align cylinder to point outward
    beam.quaternion.setFromUnitVectors(
      new THREE.Vector3(0, 1, 0),
      beamDir,
    );
    markerGroup.add(beam);

    // Additional city markers (smaller)
    const iraqCities = [
      { lat: 36.191, lng: 44.009, name: "Erbil" },
      { lat: 30.508, lng: 47.783, name: "Basra" },
      { lat: 36.34, lng: 43.13, name: "Mosul" },
    ];
    iraqCities.forEach((city) => {
      const pos = latLngToVector3(city.lat, city.lng, 1.0);
      const dot = new THREE.Mesh(
        new THREE.SphereGeometry(0.012, 12, 12),
        new THREE.MeshBasicMaterial({
          color: markerColor,
          transparent: true,
          opacity: 0.7,
        }),
      );
      dot.position.copy(pos);
      markerGroup.add(dot);
    });

    /* ── Starfield ── */
    if (isDark) {
      const starCount = 1500;
      const starPositions = new Float32Array(starCount * 3);
      for (let i = 0; i < starCount; i++) {
        const r = 15 + Math.random() * 30;
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos(2 * Math.random() - 1);
        starPositions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
        starPositions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
        starPositions[i * 3 + 2] = r * Math.cos(phi);
      }
      const starGeometry = new THREE.BufferGeometry();
      starGeometry.setAttribute("position", new THREE.BufferAttribute(starPositions, 3));
      const starMaterial = new THREE.PointsMaterial({
        color: 0xffffff,
        size: 0.05,
        transparent: true,
        opacity: 0.8,
        sizeAttenuation: true,
      });
      const stars = new THREE.Points(starGeometry, starMaterial);
      scene.add(stars);
    }

    /* ── Initial rotation to show Iraq ── */
    // Rotate so Iraq is roughly facing camera
    // Baghdad is at ~44°E longitude. To face camera, we rotate Y by -(44 + 90)° in radians
    earth.rotation.y = -((44.37 + 90) * Math.PI) / 180;

    /* ── Mouse interaction ── */
    let isDragging = false;
    let previousMouseX = 0;
    let autoRotateSpeed = 0.002;
    let targetRotation = earth.rotation.y;

    const onPointerDown = (e: PointerEvent) => {
      isDragging = true;
      previousMouseX = e.clientX;
      if (container) container.style.cursor = "grabbing";
    };
    const onPointerUp = () => {
      isDragging = false;
      if (container) container.style.cursor = "grab";
    };
    const onPointerMove = (e: PointerEvent) => {
      if (!isDragging) return;
      const delta = e.clientX - previousMouseX;
      targetRotation += delta * 0.005;
      previousMouseX = e.clientX;
    };

    container.addEventListener("pointerdown", onPointerDown);
    window.addEventListener("pointerup", onPointerUp);
    window.addEventListener("pointermove", onPointerMove);

    /* ── Resize handling ── */
    const handleResize = () => {
      if (!container) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    handleResize();
    window.addEventListener("resize", handleResize);

    /* ── Animation loop ── */
    const clock = new THREE.Clock();
    const animate = () => {
      frameRef.current = requestAnimationFrame(animate);
      const elapsed = clock.getElapsedTime();

      // Auto-rotate
      if (!isDragging) {
        targetRotation += autoRotateSpeed;
      }
      earth.rotation.y += (targetRotation - earth.rotation.y) * 0.05;

      // Clouds rotate slightly faster
      clouds.rotation.y = earth.rotation.y + elapsed * 0.0003;

      // Pulse the marker
      const pulse = 0.5 + 0.5 * Math.sin(elapsed * 3);
      glowSphere.scale.setScalar(1 + pulse * 0.6);
      glowMaterial.opacity = 0.15 + pulse * 0.25;
      markerMaterial.color.setHex(markerColor);

      // Beam pulse
      beamMaterial.opacity = 0.3 + pulse * 0.4;
      beam.scale.y = 1 + pulse * 0.3;

      // Ring pulse
      ringMaterial.uniforms.uTime.value = elapsed;

      // Update lights based on theme
      const dark = isDarkRef.current;
      ambientLight.intensity = dark ? 0.15 : 0.4;
      sunLight.intensity = dark ? 1.8 : 1.4;

      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(frameRef.current);
      container.removeEventListener("pointerdown", onPointerDown);
      window.removeEventListener("pointerup", onPointerUp);
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("resize", handleResize);
      renderer.dispose();
      scene.clear();
      try {
        if (renderer.domElement.parentNode === container) {
          container.removeChild(renderer.domElement);
        }
      } catch (_) {
        // Node already removed
      }
    };
  }, [isDark]);

  return (
    <div
      ref={containerRef}
      className="relative w-full h-full cursor-grab"
      style={{ contain: "layout paint size" }}
    />
  );
}