//VERSION=3

function setup() {
    return {
      input: [
        {
          bands: ["VV", "VH"],                  
          datasource:"S1GRD"
        },
        {
          bands: ["B03", "B12"],      
          datasource:"S2L2A"
        }
      ],
      output: [
        {
          id: "default",
          bands: 3,
          sampleType: "AUTO",        
        },    
      ],
      mosaicking: "SIMPLE",
    };
  }
  
  
  function evaluatePixel(samples) {
      var S2L2A = samples.S2L2A[0]
      var S1GRD = samples.S1GRD[0]
      var NDWI = (S2L2A.B03 - S2L2A.B12) / (S2L2A.B03 + S2L2A.B12)
      // Your javascript code here
      return {
        default: [S1GRD.VV, S1GRD.VH, NDWI],
      };
    }
  