function setup() {
    return {
      input: [{
        bands: ["SCL"],
      }],
      output: {
        id: "default",
        bands: 1,
        sampleType: SampleType.INT16 //floating point values are automatically rounded to the nearest integer by the service.
      }
    }
  }
  
  function evaluatePixel(sample) {
    return [sample.SCL, sample.B04, sample.B03, sample.B02]
  }