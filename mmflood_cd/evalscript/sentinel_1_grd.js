//VERSION=3

function setup() {
    return {
      input: [
        {
          bands: ["VV", "VH"],
        }
      ],
      output: [
        {
          id: "default",
          bands: 2,
          sampleType: "FLOAT32",
        }
      ],
      mosaicking: "Tile",
    };
  }
  
  function evaluatePixel(samples) {
    // Your JavaScript code here
    return {
      default: [samples[0].VV, samples[0].VH],
    };
  }
  