include "globals.mzn";

int: nLoci;
int: nGametes;
set of int: NLoci = 1..nLoci;
set of int: NLociDiff = NLoci diff {1};
set of int: NGametes = 1..nGametes;
set of int: NGametesOpt = {0} union NGametes;
int: maxCrossovers;

int: nTreeCells;
set of int: NTreeCells = 1..nTreeCells;

enum NodeType = {Node, Leaf, Null};
array[NTreeCells] of var NodeType: treeType;
array[NTreeCells] of var NTreeCells union {0}: treeLeft;
array[NTreeCells] of var NTreeCells union {0}: treeRight;

% Tree structure
constraint increasing(treeType);
constraint forall (i in NTreeCells where treeType[i] == Node) (
  treeLeft[i] > i /\
  treeRight[i] > i /\
  treeType[treeLeft[i]] != Null /\
  treeType[treeRight[i]] != Null /\
  true
);
constraint forall (i in NTreeCells where treeType[i] != Node) (
  treeLeft[i] = 0 /\ treeRight[i] = 0
);

set of int: B = 0..1;
array[NGametes, NLoci] of B: gametes;
array[NTreeCells, NLoci] of var B: xs;

array[NTreeCells] of var NGametesOpt: index;
constraint forall (i in NTreeCells) (
  (treeType[i] = Leaf <-> index[i] > 0) /\
  (treeType[i] = Null <-> xs[i, NLoci] = [0 | _ in NLoci])
);
constraint all_different_except_0(index);

constraint forall (i in NTreeCells where treeType[i] == Leaf) (
  forall (j in NLoci) (
    xs[i, j] = gametes[index[i], j]
  )
);


% First plant is the desired plant
constraint xs[1, NLoci] == [1 | _ in NLoci] /\ treeType[1] != Null;

% Each internal node and its child nodes (genetic parents in reality)
% must be related by crossing
array[NTreeCells, NLoci] of var 1..2: source;
array[NTreeCells, NLociDiff] of var 0..1: swap;
constraint forall (i in NTreeCells) (
  if treeType[i] = Node then
    crossedGamete(
      treeLeft[i],
      treeRight[i],
      i,
    )
  else
    forall (j in NLoci) (source[i, j] = 1) /\
    forall (j in NLociDiff) (swap[i, j] = 0)
  endif
);

predicate crossedGamete(
  var NTreeCells: igx,
  var NTreeCells: igy,
  NTreeCells: igz,
) = (
  let {
    constraint forall (j in NLoci diff {1}) (
      swap[igz,j] = 1 <-> source[igz,j-1] != source[igz,j]
    );
    constraint sum(swap[igz, ..]) <= maxCrossovers;
    % redundant constraint
    constraint count(swap[igz, ..], 1) <= maxCrossovers;

  } in forall (j in NLoci) (
    xs[igz, j] = [xs[igx, j], xs[igy, j]][source[igz, j]]
  )
);

var 0..nTreeCells: objective = count(treeType, Node);

int: BlocksNumber = 6 ;
string: Group_1 = "array1d(xs)";
string: Group_2 = "treeType";
string: Group_3 = "treeLeft";
string: Group_4 = "treeRight";
string: Group_5 = "array1d(source)";
string: Group_6 = "array1d(swap)";

ann: varsel;
ann: valsel;

solve :: int_search(
  array1d(xs) ++
    treeType ++
    treeLeft ++
    treeRight ++
    array1d(source) ++
    array1d(swap),
    varsel,
    valsel
) minimize objective;

predicate notDomBy(var NTreeCells: igx, var NTreeCells: igy) = (
  exists(j in NLoci) (xs[igx, j] > xs[igy, j])
);

constraint symmetry_breaking_constraint(
  forall (i in NTreeCells where treeType[i] == Node) (
    %treeLeft[i] < treeRight[i] /\
    notDomBy(i, treeRight[i]) /\
    notDomBy(i, treeLeft[i]) /\
    notDomBy(treeLeft[i], treeRight[i]) /\
    notDomBy(treeRight[i], treeLeft[i]) /\
    true
  )
);
