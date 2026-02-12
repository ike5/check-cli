# Homebrew formula for check-cli
# 
# To use this formula:
# 1. Create a tap repository: github.com/yourusername/homebrew-check-cli
# 2. Put this file at Formula/check-cli.rb
# 3. Users can then install with: brew tap yourusername/check-cli && brew install check-cli
#
# Update the url and sha256 when releasing new versions

class CheckCli < Formula
  include Language::Python::Virtualenv

  desc "Beautiful CLI tool to test internet speed, latency, jitter, and more"
  homepage "https://github.com/ike5/check-cli"
  url "https://files.pythonhosted.org/packages/source/c/check-cli/check_cli-1.0.0.tar.gz"
  sha256 "UPDATE_THIS_WITH_ACTUAL_SHA256_AFTER_PUBLISHING_TO_PYPI"
  license "MIT"

  depends_on "python@3.11"

  resource "httpx" do
    url "https://files.pythonhosted.org/packages/source/h/httpx/httpx-0.27.0.tar.gz"
    sha256 "UPDATE_WITH_ACTUAL_SHA256"
  end

  resource "rich" do
    url "https://files.pythonhosted.org/packages/source/r/rich/rich-13.7.0.tar.gz"
    sha256 "UPDATE_WITH_ACTUAL_SHA256"
  end

  resource "click" do
    url "https://files.pythonhosted.org/packages/source/c/click/click-8.1.7.tar.gz"
    sha256 "UPDATE_WITH_ACTUAL_SHA256"
  end

  resource "platformdirs" do
    url "https://files.pythonhosted.org/packages/source/p/platformdirs/platformdirs-4.1.0.tar.gz"
    sha256 "UPDATE_WITH_ACTUAL_SHA256"
  end

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match "check-cli", shell_output("#{bin}/check --version")
  end
end
