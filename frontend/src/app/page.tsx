import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import HeroSection from "@/components/sections/HeroSection";

export default function Home() {
  return (
    <>
      <Navbar />
      <main>
        <HeroSection />

        {/* Featured Projects Section placeholder */}
        <section className="section-padding bg-gray-50 dark:bg-dark-surface/30">
          <div className="container-custom">
            <h2 className="text-3xl font-bold text-center text-gray-900 dark:text-white mb-4">
              Featured Projects
            </h2>
            <p className="text-center text-gray-600 dark:text-gray-400 mb-12 max-w-2xl mx-auto">
              A selection of my recent work showcasing full-stack development,
              clean architecture, and modern design.
            </p>
            {/* Project cards will be rendered here */}
          </div>
        </section>

        {/* Skills Section placeholder */}
        <section className="section-padding">
          <div className="container-custom">
            <h2 className="text-3xl font-bold text-center text-gray-900 dark:text-white mb-12">
              Technical Skills
            </h2>
            {/* Skills grid will be rendered here */}
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}
