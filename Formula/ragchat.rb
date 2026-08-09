class Ragchat < Formula
  desc "Universal Documentation RAG Chatbot for Websites, Telegram, and Discord"
  homepage "https://github.com/soumen888/Rag-Chatbot"
  url "https://github.com/soumen888/Rag-Chatbot/archive/refs/heads/main.tar.gz"
  version "3.0.0"

  depends_on "python@3.11"
  depends_on "rust" => :build

  # Prevents Homebrew from trying to relocate Python native extensions
  # (e.g. orjson) inside the venv, which fails due to Mach-O header size limits
  skip_clean "libexec"

  def install
    # Copy all source files to the Homebrew execution directory
    libexec.install Dir["*"]

    # Create a virtual environment inside the cell
    system "python3.11", "-m", "venv", "#{libexec}/venv"

    # Install Python requirements
    # We compile orjson from source with extra header padding so Homebrew can relocate its dylibs
    ENV["LDFLAGS"] = "-Wl,-headerpad_max_install_names"
    system "#{libexec}/venv/bin/pip", "install", "--upgrade", "pip"
    system "#{libexec}/venv/bin/pip", "install", "--no-binary", "orjson", "-r", "#{libexec}/requirements.txt"

    # Create a native executable wrapper in the bin directory
    (bin/"ragchat").write <<~EOS
      #!/bin/bash
      cd "#{libexec}"
      exec "./venv/bin/python" "main.py" "$@"
    EOS
  end

  test do
    # Simple check to see if the command responds
    assert_match "Universal Documentation Chat", shell_output("#{bin}/ragchat", 1)
  end
end
