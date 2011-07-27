#include "cudastatic.hpp"
#include "cudastate.hpp"
double* localVector;
double* localMatrix;
double* globalVector;
double* globalMatrix;
double* solutionVector;
int* Tracer_findrm;
int Tracer_findrm_size;
int* Tracer_colm;
int Tracer_colm_size;
int* t_adv_findrm;
int t_adv_findrm_size;
int* t_adv_colm;
int t_adv_colm_size;


__global__ void A(double* localTensor, int n_ele, double dt, double* detwei, double* CG1, double* d_CG1)
{
  for(int i_ele = THREAD_ID; i_ele < n_ele; i_ele += THREAD_COUNT)
  {
    for(int i_r_0 = 0; i_r_0 < 3; i_r_0++)
    {
      for(int i_r_1 = 0; i_r_1 < 3; i_r_1++)
      {
        localTensor[((i_ele + n_ele * i_r_0) + 3 * n_ele * i_r_1)] = 0.0;
        for(int i_g = 0; i_g < 6; i_g++)
        {
          localTensor[((i_ele + n_ele * i_r_0) + 3 * n_ele * i_r_1)] += CG1[(i_r_0 + 3 * i_g)] * CG1[(i_r_1 + 3 * i_g)] * detwei[(i_ele + n_ele * i_g)];
          for(int i_d_0 = 0; i_d_0 < 2; i_d_0++)
          {
            localTensor[((i_ele + n_ele * i_r_0) + 3 * n_ele * i_r_1)] += -1 * 0.5 * d_CG1[(((i_ele + n_ele * i_d_0) + 2 * n_ele * i_g) + 6 * 2 * n_ele * i_r_0)] * d_CG1[(((i_ele + n_ele * i_d_0) + 2 * n_ele * i_g) + 6 * 2 * n_ele * i_r_1)] * 0.1 * -1 * dt * detwei[(i_ele + n_ele * i_g)];
          };
        };
      };
    };
  };
}

__global__ void d(double* localTensor, int n_ele, double dt, double* detwei, double* d_CG1)
{
  for(int i_ele = THREAD_ID; i_ele < n_ele; i_ele += THREAD_COUNT)
  {
    for(int i_r_0 = 0; i_r_0 < 3; i_r_0++)
    {
      for(int i_r_1 = 0; i_r_1 < 3; i_r_1++)
      {
        localTensor[((i_ele + n_ele * i_r_0) + 3 * n_ele * i_r_1)] = 0.0;
        for(int i_g = 0; i_g < 6; i_g++)
        {
          for(int i_d_0 = 0; i_d_0 < 2; i_d_0++)
          {
            localTensor[((i_ele + n_ele * i_r_0) + 3 * n_ele * i_r_1)] += d_CG1[(((i_ele + n_ele * i_d_0) + 2 * n_ele * i_g) + 6 * 2 * n_ele * i_r_0)] * d_CG1[(((i_ele + n_ele * i_d_0) + 2 * n_ele * i_g) + 6 * 2 * n_ele * i_r_1)] * 0.1 * -1 * dt * detwei[(i_ele + n_ele * i_g)];
          };
        };
      };
    };
  };
}

__global__ void M(double* localTensor, int n_ele, double dt, double* detwei, double* CG1)
{
  for(int i_ele = THREAD_ID; i_ele < n_ele; i_ele += THREAD_COUNT)
  {
    for(int i_r_0 = 0; i_r_0 < 3; i_r_0++)
    {
      for(int i_r_1 = 0; i_r_1 < 3; i_r_1++)
      {
        localTensor[((i_ele + n_ele * i_r_0) + 3 * n_ele * i_r_1)] = 0.0;
        for(int i_g = 0; i_g < 6; i_g++)
        {
          localTensor[((i_ele + n_ele * i_r_0) + 3 * n_ele * i_r_1)] += CG1[(i_r_0 + 3 * i_g)] * CG1[(i_r_1 + 3 * i_g)] * detwei[(i_ele + n_ele * i_g)];
        };
      };
    };
  };
}

__global__ void diff_rhs(double* localTensor, int n_ele, double dt, double* detwei, double* c0, double* CG1, double* d_CG1)
{
  for(int i_ele = THREAD_ID; i_ele < n_ele; i_ele += THREAD_COUNT)
  {
    double d_c_q0[12];
    double c_q0[6];
    for(int i_g = 0; i_g < 6; i_g++)
    {
      c_q0[i_g] = 0.0;
      for(int i_r_0 = 0; i_r_0 < 3; i_r_0++)
      {
        c_q0[i_g] += c0[(i_ele + n_ele * i_r_0)] * CG1[(i_r_0 + 3 * i_g)];
      };
      for(int i_d_0 = 0; i_d_0 < 2; i_d_0++)
      {
        d_c_q0[(i_g + 6 * i_d_0)] = 0.0;
        for(int i_r_0 = 0; i_r_0 < 3; i_r_0++)
        {
          d_c_q0[(i_g + 6 * i_d_0)] += c0[(i_ele + n_ele * i_r_0)] * d_CG1[(((i_ele + n_ele * i_d_0) + 2 * n_ele * i_g) + 6 * 2 * n_ele * i_r_0)];
        };
      };
    };
    for(int i_r_0 = 0; i_r_0 < 3; i_r_0++)
    {
      localTensor[(i_ele + n_ele * i_r_0)] = 0.0;
      for(int i_g = 0; i_g < 6; i_g++)
      {
        localTensor[(i_ele + n_ele * i_r_0)] += CG1[(i_r_0 + 3 * i_g)] * c_q0[i_g] * detwei[(i_ele + n_ele * i_g)];
        for(int i_d_0 = 0; i_d_0 < 2; i_d_0++)
        {
          localTensor[(i_ele + n_ele * i_r_0)] += 0.5 * d_CG1[(((i_ele + n_ele * i_d_0) + 2 * n_ele * i_g) + 6 * 2 * n_ele * i_r_0)] * d_c_q0[(i_g + 6 * i_d_0)] * 0.1 * -1 * dt * detwei[(i_ele + n_ele * i_g)];
        };
      };
    };
  };
}

__global__ void adv_rhs(double* localTensor, int n_ele, double dt, double* detwei, double* c0, double* c1, double* CG1, double* d_CG1)
{
  for(int i_ele = THREAD_ID; i_ele < n_ele; i_ele += THREAD_COUNT)
  {
    double c_q1[12];
    double c_q0[6];
    for(int i_g = 0; i_g < 6; i_g++)
    {
      c_q0[i_g] = 0.0;
      for(int i_r_0 = 0; i_r_0 < 3; i_r_0++)
      {
        c_q0[i_g] += c0[(i_ele + n_ele * i_r_0)] * CG1[(i_r_0 + 3 * i_g)];
      };
      for(int i_d_0 = 0; i_d_0 < 2; i_d_0++)
      {
        c_q1[(i_g + 6 * i_d_0)] = 0.0;
        for(int i_r_0 = 0; i_r_0 < 3; i_r_0++)
        {
          c_q1[(i_g + 6 * i_d_0)] += c1[((i_ele + n_ele * i_d_0) + 2 * n_ele * i_r_0)] * CG1[(i_r_0 + 3 * i_g)];
        };
      };
    };
    for(int i_r_0 = 0; i_r_0 < 3; i_r_0++)
    {
      localTensor[(i_ele + n_ele * i_r_0)] = 0.0;
      for(int i_g = 0; i_g < 6; i_g++)
      {
        localTensor[(i_ele + n_ele * i_r_0)] += CG1[(i_r_0 + 3 * i_g)] * c_q0[i_g] * detwei[(i_ele + n_ele * i_g)];
        for(int i_d_0 = 0; i_d_0 < 2; i_d_0++)
        {
          localTensor[(i_ele + n_ele * i_r_0)] += c_q0[i_g] * dt * c_q1[(i_g + 6 * i_d_0)] * d_CG1[(((i_ele + n_ele * i_d_0) + 2 * n_ele * i_g) + 6 * 2 * n_ele * i_r_0)] * detwei[(i_ele + n_ele * i_g)];
        };
      };
    };
  };
}

StateHolder* state;
extern "C" void initialise_gpu_()
{
  state = new StateHolder();
  state->initialise();
  state->extractField("Tracer", 0);
  state->extractField("Velocity", 1);
  state->allocateAllGPUMemory();
  state->transferAllFields();
  int numEle = state->getNumEle();
  int numNodes = state->getNumNodes();
  state->insertTemporaryField("Tracer", "t_adv");
  CsrSparsity* t_adv_sparsity = state->getSparsity("t_adv");
  t_adv_colm = t_adv_sparsity->getCudaColm();
  t_adv_findrm = t_adv_sparsity->getCudaFindrm();
  t_adv_colm_size = t_adv_sparsity->getSizeColm();
  t_adv_findrm_size = t_adv_sparsity->getSizeFindrm();
  CsrSparsity* Tracer_sparsity = state->getSparsity("Tracer");
  Tracer_colm = Tracer_sparsity->getCudaColm();
  Tracer_findrm = Tracer_sparsity->getCudaFindrm();
  Tracer_colm_size = Tracer_sparsity->getSizeColm();
  Tracer_findrm_size = Tracer_sparsity->getSizeFindrm();
  int numValsPerNode = state->getValsPerNode("Tracer");
  int numVectorEntries = state->getNodesPerEle("Tracer");
  numVectorEntries = numVectorEntries * numValsPerNode;
  int numMatrixEntries = numVectorEntries * numVectorEntries;
  cudaMalloc((void**)(&localVector), sizeof(double) * numEle * numVectorEntries);
  cudaMalloc((void**)(&localMatrix), sizeof(double) * numEle * numMatrixEntries);
  cudaMalloc((void**)(&globalVector), sizeof(double) * numNodes * numValsPerNode);
  cudaMalloc((void**)(&globalMatrix), sizeof(double) * Tracer_colm_size);
  cudaMalloc((void**)(&solutionVector), sizeof(double) * numNodes * numValsPerNode);
}

extern "C" void finalise_gpu_()
{
  delete state;
}

extern "C" void run_model_(double* dt_pointer)
{
  double dt = *dt_pointer;
  int numEle = state->getNumEle();
  int numNodes = state->getNumNodes();
  double* detwei = state->getDetwei();
  int* eleNodes = state->getEleNodes();
  double* coordinates = state->getCoordinates();
  double* dn = state->getReferenceDn();
  double* quadWeights = state->getQuadWeights();
  int nDim = state->getDimension("Coordinate");
  int nQuad = state->getNumQuadPoints("Coordinate");
  int nodesPerEle = state->getNodesPerEle("Coordinate");
  double* shape = state->getBasisFunction("Coordinate");
  double* dShape = state->getBasisFunctionDerivative("Coordinate");
  int blockXDim = 64;
  int gridXDim = 128;
  int shMemSize = t2p_shmemsize(blockXDim, nDim, nodesPerEle);
  transform_to_physical<<<gridXDim,blockXDim,shMemSize>>>(coordinates, dn, quadWeights, dShape, detwei, numEle, nDim, nQuad, nodesPerEle);
  M<<<gridXDim,blockXDim>>>(localMatrix, numEle, dt, detwei, shape);
  double* TracerCoeff = state->getElementValue("Tracer");
  double* VelocityCoeff = state->getElementValue("Velocity");
  adv_rhs<<<gridXDim,blockXDim>>>(localVector, numEle, dt, detwei, TracerCoeff, VelocityCoeff, shape, dShape);
  cudaMemset(globalMatrix, 0, sizeof(double) * t_adv_colm_size);
  cudaMemset(globalVector, 0, sizeof(double) * state->getValsPerNode("t_adv") * numNodes);
  matrix_addto<<<gridXDim,blockXDim>>>(t_adv_findrm, t_adv_colm, globalMatrix, eleNodes, localMatrix, numEle, nodesPerEle);
  vector_addto<<<gridXDim,blockXDim>>>(globalVector, eleNodes, localVector, numEle, nodesPerEle);
  cg_solve(t_adv_findrm, t_adv_findrm_size, t_adv_colm, t_adv_colm_size, globalMatrix, globalVector, numNodes, solutionVector);
  double* t_advCoeff = state->getElementValue("t_adv");
  expand_data<<<gridXDim,blockXDim>>>(t_advCoeff, solutionVector, eleNodes, numEle, state->getValsPerNode("t_adv"), nodesPerEle);
  A<<<gridXDim,blockXDim>>>(localMatrix, numEle, dt, detwei, shape, dShape);
  diff_rhs<<<gridXDim,blockXDim>>>(localVector, numEle, dt, detwei, t_advCoeff, shape, dShape);
  cudaMemset(globalMatrix, 0, sizeof(double) * Tracer_colm_size);
  cudaMemset(globalVector, 0, sizeof(double) * state->getValsPerNode("Tracer") * numNodes);
  matrix_addto<<<gridXDim,blockXDim>>>(Tracer_findrm, Tracer_colm, globalMatrix, eleNodes, localMatrix, numEle, nodesPerEle);
  vector_addto<<<gridXDim,blockXDim>>>(globalVector, eleNodes, localVector, numEle, nodesPerEle);
  cg_solve(Tracer_findrm, Tracer_findrm_size, Tracer_colm, Tracer_colm_size, globalMatrix, globalVector, numNodes, solutionVector);
  expand_data<<<gridXDim,blockXDim>>>(TracerCoeff, solutionVector, eleNodes, numEle, state->getValsPerNode("Tracer"), nodesPerEle);
  state->returnFieldToHost("Tracer");
}



