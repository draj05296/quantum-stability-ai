import heroImage from "../assets/hero.png";

function Hero() {
  return (
    <section className="hero" id="home">
      <div className="hero-text">
        <h1>
          Quantum State <span className="gradient-text">Fidelity Index</span>
        </h1>

        <p className="hero-subtitle">
          AI-powered quantum stability analysis and intelligent qubit
          recommendation, built on real IBM Quantum research.
        </p>

        <div className="hero-buttons">
          <a href="#dashboard" className="btn btn-primary">
            Explore Dashboard
          </a>
          <a href="#features" className="btn btn-secondary">
            Learn More
          </a>
        </div>
      </div>

      <div className="hero-visual">
        <img src={heroImage} alt="Quantum computing illustration" />
      </div>
    </section>
  );
}

export default Hero;
