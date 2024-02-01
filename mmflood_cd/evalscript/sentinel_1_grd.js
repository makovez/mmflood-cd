//VERSION=3

function setup() {
    return {
      input: [
        {
          bands: ["VV", "VH"],
          metadata: ["bounds"],
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
  
  function updateOutputMetadata(scenes, inputMetadata, outputMetadata) {
    outputMetadata.userData = {
      "inputMetadata": inputMetadata
    }
    outputMetadata.userData["scenes"] = scenes
  }
  
  function evaluatePixel(samples) {
    // Your JavaScript code here
    return {
      default: [samples[0].VV, samples[0].VH],
    };
  }
  